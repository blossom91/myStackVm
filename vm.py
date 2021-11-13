from instruction import MachineCode


log = print


class Registers:
    def __init__(self):
        self.pa = 0


class Stack:
    def __init__(self):
        self.data = []

    def push(self, element):
        self.data.append(element)

    def pop(self):
        return self.data.pop(-1)

    def top(self, offset=0):
        return self.data[-1 - offset]

    def replace(self, offset, value):
        self.data[-1 - offset] = value


class StackVirtualMachine:
    def __init__(self):
        # 寄存器只有一个 pa，持有下一条指令地址
        self.registers = Registers()

        # operand_stack 用于充当各种原生指令的操作数暂存区，
        # 比如
        # add 指令操作的两个输入从这里 pop 出来，
        # 得到结果 push 到栈顶
        self.operand_stack = Stack()

        # 存放调用子过程结束后的返回地址
        self.return_stack = Stack()

        # 存放局部变量
        self.variable_stack = Stack()

        # 调用函数时，用于暂存参数
        self.parameter_stack = Stack()

        # 调用函数时，用于暂存参数
        self.return_value_stack = Stack()

    def setup_memory(self, memory):
        self.memory = memory

    def run(self):
        while True:
            instruction = self.memory[self.registers.pa]
            if instruction == MachineCode.halt:
                log('halt')
                log('self.operand_stack', self.operand_stack.data)
                log('self.variable_stack', self.variable_stack.data)
                log('self.parameter_stack', self.parameter_stack.data)
                log('self.return_value_stack', self.return_value_stack.data)
                break

            process = self.process_function_selector(instruction)
            process()

    def process_function_selector(self, instruction):
        d = {
            MachineCode.push: self.push,
            MachineCode.pop: self.pop,

            MachineCode.save_to_memory: self.save_to_memory,
            MachineCode.load_from_memory: self.load_from_memory,

            MachineCode.add: self.add,
            MachineCode.compare: self.compare,
            MachineCode.jump_if_great: self.jump_if_great,
            MachineCode.jump_if_less: self.jump_if_less,
            MachineCode.jump: self.jump,

            MachineCode.swap: self.swap,

            MachineCode.subroutine_call: self.subroutine_call,
            MachineCode._exit: self._exit,

            MachineCode.push_variable_stack: self.push_variable_stack,
            MachineCode.pop_variable_stack: self.pop_variable_stack,
            MachineCode.load_from_variable_stack: self.load_variable_stack,
            MachineCode.save_to_variable_stack: self.save_to_variable_stack,

            MachineCode.push_parameter_stack: self.push_parameter_stack,
            MachineCode.pop_parameter_stack: self.pop_parameter_stack,

            MachineCode.push_return_value_stack: self.push_return_value_stack,
            MachineCode.pop_return_value_stack: self.pop_return_value_stack,
        }
        return d[instruction]

    def push(self):
        element = int(self.memory[self.registers.pa + 1])
        self.operand_stack.push(element)
        self.registers.pa += 2
        log(f'push <element ({element})>')

    def pop(self):
        element = self.operand_stack.pop()
        self.registers.pa += 1
        log(f'pop <element ({element})>')

    def add(self):
        b = self.operand_stack.pop()
        a = self.operand_stack.pop()
        _sum = a + b
        self.operand_stack.push(_sum)
        self.registers.pa += 1
        log(f'add <a ({a}) b ({b})>')

    def save_to_memory(self):
        value = self.operand_stack.pop()
        address = self.operand_stack.pop()
        self.memory[address] = value
        self.registers.pa += 1
        log(f'save_to_memory <address ({address}) value ({value})>')

    def load_from_memory(self):
        memory_address = self.operand_stack.pop()
        value = self.memory[memory_address]
        self.operand_stack.push(value)
        self.registers.pa += 1
        log(f'load_from_memory <a {memory_address}> <v {value}>')

    def compare(self):
        b = self.operand_stack.pop()
        a = self.operand_stack.pop()
        result = None
        if a > b:
            result = 2
        elif a == b:
            result = 1
        else:
            result = 0

        self.operand_stack.push(result)
        self.registers.pa += 1
        log(f'compare <a ({a}) b ({b}) result ({result})>')

    def jump(self):
        address = self.operand_stack.pop()
        self.registers.pa = address
        log(f'jump <address ({address})>')

    def jump_if_great(self):
        address = self.operand_stack.pop()
        condition = self.operand_stack.pop()
        if condition == 2:
            self.registers.pa = address
        else:
            self.registers.pa += 1
        log(f'jump_if_great <condition ({condition}) address ({address})>')

    def jump_if_less(self):
        address = self.operand_stack.pop()
        condition = self.operand_stack.pop()
        if condition == 0:
            self.registers.pa = address
        else:
            self.registers.pa += 1
        log(f'jump_if_less <condition ({condition}) address ({address})>')

    def swap(self):
        top = self.operand_stack.pop()
        second = self.operand_stack.pop()
        self.operand_stack.push(top)
        self.operand_stack.push(second)
        self.registers.pa += 1
        log(f'swap <top ({top}) second ({second})>')

    def subroutine_call(self):
        subroutine_address = self.operand_stack.pop()
        return_address = self.registers.pa + 1
        self.return_stack.push(return_address)
        self.registers.pa = subroutine_address
        log(f'subroutine_call <address ({subroutine_address})>')

    def _exit(self):
        return_address = self.return_stack.pop()
        self.registers.pa = return_address
        log(f'exit <return_address ({return_address})>')

    def push_variable_stack(self):
        element = self.operand_stack.pop()
        self.variable_stack.push(element)
        self.registers.pa += 1
        log(f'push_variable_stack <element ({element})>')

    def pop_variable_stack(self):
        element = self.variable_stack.pop()
        self.operand_stack.push(element)
        self.registers.pa += 1
        log(f'pop_variable_stack <element ({element})>')

    def load_variable_stack(self):
        offset = self.operand_stack.pop()
        value = self.variable_stack.top(offset)
        self.operand_stack.push(value)
        self.registers.pa += 1
        log(f'load_variable_stack <offset ({offset}) value ({value})>')

    def save_to_variable_stack(self):
        offset = self.operand_stack.pop()
        value = self.operand_stack.pop()
        self.variable_stack.replace(offset, value)
        self.registers.pa += 1
        log(f'save_to_variable_stack <offset ({offset}), value ({value})>')

    def push_parameter_stack(self):
        element = self.operand_stack.pop()
        self.parameter_stack.push(element)
        self.registers.pa += 1
        log(f'push_parameter_stack <element ({element})>')

    def pop_parameter_stack(self):
        element = self.parameter_stack.pop()
        self.operand_stack.push(element)
        self.registers.pa += 1
        log(f'pop_parameter_stack <element ({element})>')

    def push_return_value_stack(self):
        element = self.operand_stack.pop()
        self.return_value_stack.push(element)
        self.registers.pa += 1
        log(f'push_return_value_stack <element ({element})>')

    def pop_return_value_stack(self):
        element = self.return_value_stack.pop()
        self.operand_stack.push(element)
        self.registers.pa += 1
        log(f'pop_return_value_stack <element ({element})>')
