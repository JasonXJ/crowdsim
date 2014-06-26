import readline

class interactiveTester:
    def __init__(self):
        self.command_func_print = []
        self.prompt = '>>> '
        self.resultPrompt = '>>>>>> '
        self.exitCommand = 'exit'

    def boundCommand(self, commandPrefix, func, printResult = False):
        self.command_func_print.append((commandPrefix, func, printResult))

    def setPrompt(self, prompt):
        self.prompt = prompt

    def setResultPrompt(self, prompt):
        self.resultPrompt = prompt
    
    def setExitCommand(self, command):
        self.exitCommand = command

    def start(self):
        while True:
            x = input(self.prompt)
            if x == self.exitCommand:
                break
            hit = False
            for command, func, p in self.command_func_print:
                args = x[len(command):].split()
                if x.startswith(command):
                    hit = True
                    r = func(*args)
                    if p:
                        print(self.resultPrompt + str(r))
            if hit == False:
                print('what ?')
