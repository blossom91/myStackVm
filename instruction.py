class Instruction:
    # 约定，栈顶叫 top，栈顶第二个元素叫 second

    # push 到 operand stack
    push = 'push'
    pop = 'pop'

    # operand stack 的 top 作为 value
    # operand stack 的 second 作为 address
    # 都 pop 出来，然后赋值 memory[address] = value
    save_to_memory = 'save_to_memory'

    # top 放着内存地址 address
    # pop 出来，取到值，push 到栈顶
    load_from_memory = 'load_from_memory'

    # 虚拟机停机
    halt = 'halt'

    # pop 出 operand stack 的栈顶两个元素
    # 相加之后，结果 push 到 operand stack 栈顶
    add = 'add'

    # pop 栈顶两个元素进行比较，比较顺序是 second - top
    # 比较结果 push 到栈顶，
    # 2 代表大于
    # 1 代表等于
    # 0 代表小于
    compare = 'compare'

    # second 存放着比较结果
    # top 存放着将要跳转的地址
    # 如果结果是大于，就跳转到指定地址
    jump_if_great = 'jump_if_great'

    jump_if_less = 'jump_if_less'

    # 无条件跳转
    jump = 'jump'

    # 栈顶两个元素交换位置
    swap = 'swap'

    # 调用子过程，operand 栈顶是子过程的地址
    # 在跳转之前，虚拟机自动把下一条指令地址 push 到 return stack
    subroutine_call = 'subroutine_call'

    # 执行 exit，子过程结束，
    # 从 return stack 中 pop 出返回地址，跳转
    _exit = 'exit'

    # operand stack 的 top 放着值，pop 出来
    # push 到 variable stack
    push_variable_stack = 'push_variable_stack'
    # variable stack 的栈顶 pop 出来，push 到 operand stack
    pop_variable_stack = 'pop_variable_stack'

    # operand stack 的 top 放着偏移 offset
    # variable stack 对应偏移的值复制出来，push 到 operand stack
    load_from_variable_stack = 'load_from_variable_stack'

    # operand stack 的 top 放着偏移 offset
    # operand stack 的 second 放着值 value
    # 都 pop 出来，
    # 将 variable stack 对应偏移的值覆盖
    save_to_variable_stack = 'save_to_variable_stack'

    # operand stack 的 top 放着值，pop 出来
    # push 到 parameter stack
    push_parameter_stack = 'push_parameter_stack'
    # parameter stack 的栈顶 pop 出来，push 到 operand stack
    pop_parameter_stack = 'pop_parameter_stack'

    # operand stack 的 top 放着值，pop 出来
    # push 到 return value stack
    push_return_value_stack = 'push_return_value_stack'
    # return value stack 的栈顶 pop 出来，push 到 operand stack
    pop_return_value_stack = 'pop_return_value_stack'


class MachineCode:
    # 数字是随便定的，加指令要检查，避免不小心数字重复
    push = 0b00000000
    pop = 0b00000001

    save_to_memory = 0b00000011
    load_from_memory = 0b00000101

    halt = 0b00000100

    add = 0b00000010

    compare = 0b00001001
    jump_if_great = 0b00001000
    jump = 0b00000111

    swap = 0b00010111

    subroutine_call = 0b00001010
    _exit = 0b00001011

    push_variable_stack = 0b00010000
    pop_variable_stack = 0b00010001
    load_from_variable_stack = 0b00010010
    save_to_variable_stack = 0b00010011

    push_parameter_stack = 0b00001100
    pop_parameter_stack = 0b00001101

    pop_return_value_stack = 0b00001110
    push_return_value_stack = 0b00001111

    jump_if_less = 0b00011000


def instruction_to_machine_code_mapping():
    d = {
        Instruction.push: MachineCode.push,
        Instruction.pop: MachineCode.pop,

        Instruction.save_to_memory: MachineCode.save_to_memory,
        Instruction.load_from_memory: MachineCode.load_from_memory,

        Instruction.halt: MachineCode.halt,

        Instruction.add: MachineCode.add,
        Instruction.compare: MachineCode.compare,
        Instruction.jump_if_great: MachineCode.jump_if_great,
        Instruction.jump_if_less: MachineCode.jump_if_less,
        Instruction.jump: MachineCode.jump,

        Instruction.subroutine_call: MachineCode.subroutine_call,
        Instruction._exit: MachineCode._exit,

        Instruction.push_variable_stack: MachineCode.push_variable_stack,
        Instruction.pop_variable_stack: MachineCode.pop_variable_stack,
        Instruction.load_from_variable_stack: MachineCode.load_from_variable_stack,
        Instruction.save_to_variable_stack: MachineCode.save_to_variable_stack,

        Instruction.swap: MachineCode.swap,

        Instruction.push_parameter_stack: MachineCode.push_parameter_stack,
        Instruction.pop_parameter_stack: MachineCode.pop_parameter_stack,

        Instruction.pop_return_value_stack: MachineCode.pop_return_value_stack,
        Instruction.push_return_value_stack: MachineCode.push_return_value_stack,
    }
    return d

