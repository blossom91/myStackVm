from assembler import Assembler
from screen import Screen
from vm import StackVirtualMachine
from multiprocessing import Process, Array


log = print


def run_screen(memory):
    # Screen 是固定的套路，不用知道怎么实现
    # 指定显存开始位置是内存地址 51200，规定
    # pixel_width 表示一行可以放几个像素，pixel_height 同理
    screen = Screen(pixel_width=10, pixel_height=10, memory=memory, start_index=51200)
    screen.run()


def run_vm(memory):
    # 虚拟机
    m = StackVirtualMachine()
    # 加载内存
    m.setup_memory(memory)
    # 运行
    m.run()


def test_while():
    # 汇编程序源码
    with open('program_files/while.stack', 'r', encoding='UTF-8') as f:
        program = f.read()

    # 汇编器
    a = Assembler()
    # 汇编程序翻译成机器码序列，再往后补到 64k 作为内存
    memory = a.compile(program)

    # 由于 mac pygame 不能当子线程运行，
    # 所以要用多进程运行
    # 进程间共享数组需要用 Array 包起来，i 表示数组里都是数字
    shared_memory = Array('i', memory)

    # 屏幕运行
    screen_process = Process(target=run_screen, args=(shared_memory,))
    screen_process.start()

    # 虚拟机运行
    vm_process = Process(target=run_vm, args=(shared_memory,))
    vm_process.start()


if __name__ == '__main__':
    test_while()
