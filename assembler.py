from instruction import instruction_to_machine_code_mapping
from typing import List

log = print


class Vars:
    def __init__(self):
        self.symbol_stack = [{}]

    def offset_by_name(self, var_name):
        for frame in reversed(self.symbol_stack):
            if var_name in frame:
                return frame[var_name]
        raise NameError('未定义变量名: ', var_name)

    def push_variable(self, var_name):
        if var_name in self.symbol_stack[-1]:
            raise Exception(f'重复定义 ({var_name})')

        # 原 variable stack 里的变量的偏移 +1
        for symbol in self.symbol_stack:
            for k in symbol:
                symbol[k] += 1
        # 新变量的偏移为 0
        self.symbol_stack[-1][var_name] = 0

    def block_enter(self):
        self.symbol_stack.append({})

    def block_leave(self):
        # 获得将要退出的作用域里的变量数 num_to_pop
        num_to_pop = len(self.symbol_stack[-1])

        # 删掉当前作用域
        self.symbol_stack.pop()

        # 原 variable stack 里的变量的偏移都朝栈顶方向移动，
        # 变化量是 num_to_pop
        for symbol in self.symbol_stack:
            for k in symbol:
                symbol[k] -= num_to_pop


class Assembler:
    # 功能
    #   去掉代码前后空格
    #   去掉空行
    #   去掉整行的注释
    #   去掉行尾的注释
    #   展开伪指令
    #   标签替换为地址
    #   汇编代码转成机器码

    def __init__(self):
        self.vars = Vars()

    def compile(self, program):
        instructions = self.preprocess(program)

        # 展开伪指令
        instructions = self.extend_fake_instructions(instructions)

        # 记录标签定义，标签名 -> 地址
        instructions, definition = self.label_definition(instructions)
        # 标签替换为地址
        instructions = self.replace_labels_usage(instructions, definition)

        machine_codes = self.to_machine_codes(instructions)
        return machine_codes + [0] * (64 * 1024 - len(machine_codes))

    def extend_fake_instructions(self, instructions):
        res = []
        i = 0
        while i < len(instructions):
            ins = instructions[i]
            # 如果指令以 '.' 开头，就是伪指令
            if ins.startswith('.'):
                # 选择处理伪指令的方法
                process = self.fake_instruction_processor_selector(ins)

                # end_index 这一次处理伪指令达到的最后一行的位置
                # 用于跳过
                extended, end_index = process(instructions, i)
                res.extend(extended)
                i = end_index + 1
            else:
                res.append(ins)
                i += 1
        return res

    def fake_instruction_processor_selector(self, fake_instruction):
        signature = fake_instruction.split()[0]
        d = {
            '.var': self.fake_instruction_var,
            '.add': self.fake_instruction_add,
            '.var_to_operand_stack': self.fake_instruction_var_to_operand_stack,

            '.function': self.fake_instruction_function_definition,
            '.call': self.fake_instruction_function_call,
            '.return': self.fake_instruction_return,

            '.if': self.fake_instruction_if,
            '.while': self.fake_instruction_while,
        }
        return d[signature]

    def fake_instruction_var(self, instructions, index):
        fake = instructions[index]

        name = fake.split()[1]
        value = fake.split()[2]

        self.vars.push_variable(name)

        template = f'''
            push
            {value}
            push_variable_stack
        '''

        # 模板代码汇编代码块也做一次 preprocess 处理，
        # 去掉空格注释等无用内容，并转化为多行
        separate_instructions = self.preprocess(template)
        extended = separate_instructions

        end_index = index
        return extended, end_index

    def fake_instruction_add(self, instructions, index):
        fake = instructions[index]
        var_name_1 = fake.split()[1]
        var_name_2 = fake.split()[2]
        var_name_sum = fake.split()[3]
        extended = []

        offset_1 = self.vars.offset_by_name(var_name_1)
        offset_2 = self.vars.offset_by_name(var_name_2)
        offset_sum = self.vars.offset_by_name(var_name_sum)

        template = f'''
            push
            {offset_1}
            load_from_variable_stack
            push
            {offset_2}
            load_from_variable_stack
            add

            push
            {offset_sum}
            save_to_variable_stack
        '''
        separate_instructions = self.preprocess(template)
        extended.extend(separate_instructions)

        end_index = index
        return extended, end_index

    def fake_instruction_var_to_operand_stack(self, instructions, index):
        fake = instructions[index]
        var_name = fake.split()[1]
        extended = []

        offset = self.vars.offset_by_name(var_name)

        template = f'''
            push
            {offset}
            load_from_variable_stack
        '''
        separate_instructions = self.preprocess(template)
        extended.extend(separate_instructions)

        end_index = index
        return extended, end_index

    def fake_instruction_function_definition(self, instructions, index):
        log('vars before enter', self.vars.symbol_stack)
        # 进入函数作用域
        self.vars.block_enter()
        log('vars after  enter', self.vars.symbol_stack)

        fake = instructions[index]
        function_name = fake.split()[1]

        # 函数名作为标签
        extended = ['#' + function_name]

        # 跳过 [.function 函数名] 这一句
        index += 1

        # 把函数参数都从 parameter stack 中 pop 出来，push 到 variable stack
        parameters = []
        if len(fake.split()) > 2:
            parameters.extend(fake.split()[2:])
        for p in parameters:
            # vars 跟踪变量名和偏移
            self.vars.push_variable(p)
            # 实际上是值 push 到 variable stack 里
            template = f'''
                pop_parameter_stack
                push_variable_stack
            '''
            parameter_instructions = self.preprocess(template)
            extended.extend(parameter_instructions)

        # 收集函数体里的命令，'.function_end' 作为函数体结束的标志
        func_body_instructions = []
        next_instruction = instructions[index]

        # 如果有嵌套的函数定义，
        # 要防止内部的 ".function_end" 被误认为整个函数体的结束标志
        # 所以加一个计数来正确配对 .function 和 .function_end
        nested_count = 0

        while True:
            if next_instruction == '.function_end' and nested_count == 0:
                break
            elif next_instruction == '.function_end' and nested_count > 0:
                nested_count -= 1

            if next_instruction.split()[0] == '.function':
                nested_count += 1
            func_body_instructions.append(next_instruction)
            index += 1
            next_instruction = instructions[index]
        # 因为函数体内部的指令也可以是伪指令，所以要递归展开伪指令
        func_body_instructions = self.extend_fake_instructions(func_body_instructions)
        extended.extend(func_body_instructions)

        log('vars before leave', self.vars.symbol_stack)
        # 退出函数作用域
        self.vars.block_leave()
        log('vars after  leave', self.vars.symbol_stack)

        end_index = index
        return extended, end_index
        # 翻译例子程序 block.stack 的 log
        # vars before enter [{}]
        # vars after  enter [{}, {}]
        # vars before enter [{}, {'a': 0}]
        # vars after  enter [{}, {'a': 0}, {}]
        # vars before leave [{}, {'a': 0}, {'b': 0}]
        # vars after  leave [{}, {'a': 0}]
        # vars before leave [{}, {'a': 0}]
        # vars after  leave [{}]

    def fake_instruction_function_call(self, instructions, index):
        fake = instructions[index]
        function_name = fake.split()[1]
        extended = []

        parameters = []
        # 记录参数的变量名字
        if len(fake.split()) > 2:
            parameters.extend(fake.split()[2:])

        # 跳转到函数之前，把参数 push 到 parameter stack
        # 把参数按反序 push 到 parameter stack，正反看喜好
        parameters.reverse()
        for p in parameters:
            offset = self.vars.offset_by_name(p)
            template = f'''
               push
               {offset} 
               load_from_variable_stack
               push_parameter_stack
            '''
            push_parameters_instructions = self.preprocess(template)
            extended.extend(push_parameters_instructions)

        template = f'''
            push
            @{function_name}
            subroutine_call
        '''

        subroutine_call_instructions = self.preprocess(template)
        extended.extend(subroutine_call_instructions)

        end_index = index
        return extended, end_index

    def fake_instruction_return(self, instructions, index):
        fake = instructions[index]
        extended = []

        # 展开有返回值的情况
        if len(fake.split()) > 1:
            return_var_name = fake.split()[1]
            offset = self.vars.offset_by_name(return_var_name)
            template = f'''
                push
                {offset}
                load_from_variable_stack
                push_return_value_stack
            '''
            return_instructions = self.preprocess(template)
            extended.extend(return_instructions)

        # 删除在函数里新增的所有变量
        # 通过 vars 里的记录可得到
        for i in range(len(self.vars.symbol_stack[-1])):
            template = f'''
                pop_variable_stack
                pop
            '''
            delete_variable_instructions = self.preprocess(template)
            extended.extend(delete_variable_instructions)

        extended.append('exit')
        end_index = index
        return extended, end_index

    def fake_instruction_if(self, instructions, index):
        fake = instructions[index]

        # 进入作用域
        self.vars.block_enter()
        # 先定死 operand_1 是变量，operand_2 是数字
        # 先定死是 if (变量 > 数字)
        operand_1 = fake.split()[1]
        operand_2 = fake.split()[3]
        operand_1_offset = self.vars.offset_by_name(operand_1)

        extended = []

        # 展开 if 的条件比较部分，选择要不要跳转到 if 块里的代码
        head_template = f'''
            #if
                push
                {operand_1_offset}
                load_from_variable_stack
                push
                {operand_2}
                compare

                // 如果大于，跳转去执行 if 块里的代码
                push
                @then
                jump_if_great

                // 否则，跳过这个 if 
                push
                @endif
                jump
        '''
        condition_instructions = self.preprocess(head_template)
        extended.extend(condition_instructions)

        # 收集 if 块里的命令，'.if_end' 作为函数体结束的标志
        if_body_instructions = []
        if_body_instructions.append('#then')
        if_index = index + 1
        next = instructions[if_index]
        while next != '.if_end':
            if_body_instructions.append(next)
            if_index += 1
            next = instructions[if_index]

        # 块里的代码也可以有伪指令，展开
        if_body_instructions = self.extend_fake_instructions(if_body_instructions)
        extended.extend(if_body_instructions)

        # 清空在 if 块里新定义的变量
        pop_instructions = []
        for var in self.vars.symbol_stack[-1]:
            pop_instructions.append('pop_variable_stack')
            pop_instructions.append('pop')
        extended.extend(pop_instructions)

        # 退出 if 作用域
        self.vars.block_leave()

        # if 块结束标签
        tail_template = f'''
            #endif
        '''
        tail_instructions = self.preprocess(tail_template)
        extended.extend(tail_instructions)

        end_index = if_index
        return extended, end_index

    def fake_instruction_while(self, instructions, index):
        fake = instructions[index]

        # 进入作用域
        self.vars.block_enter()
        # 先定死 operand_1 是变量，operand_2 是数字
        # 先定死是 while (变量 < 数字)
        operand_1 = fake.split()[1]
        operand_2 = fake.split()[3]
        operand_1_offset = self.vars.offset_by_name(operand_1)

        extended = []
        head_template = f'''
            #while_start
                // condition 判断，选择执行 while 块内容还是结束 while 
                push
                {operand_1_offset}
                load_from_variable_stack
                push
                {operand_2}
                compare
                
                // 如果条件满足（写死的条件）
                push
                @do
                jump_if_less
                
                // 不满足
                push
                @while_end
                jump
        '''
        condition_instructions = self.preprocess(head_template)
        extended.extend(condition_instructions)

        log('condition_instructions', condition_instructions)

        # 收集 while 块里的命令，'.while_end' 作为 while body 结束的标志
        while_body_instructions = []
        while_body_instructions.append('#do')
        body_index = index + 1
        next = instructions[body_index]
        while next != '.while_end':
            while_body_instructions.append(next)
            body_index += 1
            next = instructions[body_index]

        # 块里的代码也可以有伪指令，展开
        while_body_instructions = self.extend_fake_instructions(while_body_instructions)
        extended.extend(while_body_instructions)

        # 清空在 while 块里新定义的变量
        pop_instructions = []
        pop_instructions = []
        for var in self.vars.symbol_stack[-1]:
            pop_instructions.append('pop_variable_stack')
            pop_instructions.append('pop')
        extended.extend(pop_instructions)
        # 退出 while 作用域
        self.vars.block_leave()

        # while body 跑完，返回 while 开头再次检查条件
        tail_template = f'''
                // 跳转回 while 开头循环
                push
                @while_start
                jump
            #while_end
        '''
        tail_instructions = self.preprocess(tail_template)
        extended.extend(tail_instructions)

        end_index = body_index
        return extended, end_index

    def label_definition(self, instructions):
        definition = {}
        new_instructions = []
        for i in instructions:
            if not i.startswith('#'):
                new_instructions.append(i)
            else:
                label_name = i[1:]
                address = len(new_instructions)
                definition[label_name] = address
        return new_instructions, definition

    def replace_labels_usage(self, instructions, definition):
        new_instructions = []
        for i in instructions:
            if i.startswith('@'):
                label_name = i[1:]
                address = definition[label_name]
                new_instructions.append(address)
            else:
                new_instructions.append(i)
        return new_instructions

    def to_machine_codes(self, instructions):
        res = []
        for i in instructions:
            if isinstance(i, int):
                res.append(i)
            elif i.isdigit():
                res.append(int(i))
            else:
                machine_code = instruction_to_machine_code_mapping()[i]
                res.append(machine_code)
        return res

    def preprocess(self, program):
        instructions = program.split('\n')
        instructions = self.remove_useless_space(instructions)
        instructions = self.remove_empty_lines(instructions)
        instructions = self.remove_whole_line_annotations(instructions)
        instructions = self.remove_tail_annotations(instructions)
        return instructions

    def remove_useless_space(self, instructions):
        res = []
        for i in instructions:
            new_i = i.strip()
            res.append(new_i)
        return res

    def remove_empty_lines(self, instructions):
        res = []
        for i in instructions:
            if i != '':
                res.append(i)
        return res

    def remove_whole_line_annotations(self, instructions):
        res = []
        for i in instructions:
            if not i.startswith('//'):
                res.append(i)
        return res

    def remove_tail_annotations(self, instructions: List[str]):
        res = []
        for i in instructions:
            annotation_start_index = i.find('//')
            if annotation_start_index == -1:
                res.append(i)
            else:
                new_i = i[:annotation_start_index]
                new_i = new_i.strip()
                res.append(new_i)
        return res
