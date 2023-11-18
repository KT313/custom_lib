import os
import sys
import importlib
import inspect
import time
import glob

def convert(func):
    def wrapper(*args, **kwargs):

        name = func.__name__
        signature = inspect.signature(func)
        string = inspect.getsource(func).lstrip("@convert\n")
        
        compiled_dir = os.path.join(os.getcwd(), "compiled")
        os.makedirs(compiled_dir, exist_ok=True)



        if glob.glob(os.path.join(compiled_dir, f"conv_{name}_code*")):
            sys.path.append(compiled_dir)
            compiled_module = importlib.import_module(f"conv_{name}_code")
            run_start = time.time()
            output = getattr(compiled_module, name)(*args, **kwargs)
            print(f"ran {name} in {(time.time()-run_start)*1000:.2f}ms")
            
            return output

        conv_start = time.time()

        # look through string for cython type information
        source_lines = string.split('\n')
        cythonized_source =  []
        for line in source_lines:
            # print(f"line: {line}")
            if "# cython:" in line:
                # Extract Cython specific comment and apply it to the source
                cython_declaration = line.split("# cython:")[1].strip()
                num_leading_spaces = len(line) - len(line.lstrip(' '))
                cythonized_source.append(" "*num_leading_spaces+cython_declaration)
            else:
                cythonized_source.append(line)
        # print(f"name: {name}\nsignature: {signature}\nstring: {string}")
        string = '\n'.join(cythonized_source)
        # print("---\n"+string)
        # save code and setup
        with open(f"conv_{name}_code.pyx", "w") as file:
            file.write(string)
        open(f"conv_{name}_setup.py", "w").write(f"""from distutils.core import setup\nfrom Cython.Build import cythonize\nsetup(\n\text_modules = cythonize("conv_{name}_code.pyx", language_level="3")\n)""")

        # do conversion
        os.makedirs("compiled", exist_ok=True)
        os.system(f"python3 conv_{name}_setup.py build_ext --inplace > /dev/null")
        filename = glob.glob(f'conv_{name}_code.cpython*')[0]
        os.system(f"mv {filename} compiled/{filename}")

        # Add the current directory to sys.path to find the compiled module
        sys.path.append(compiled_dir)
        compiled_module = importlib.import_module(f"conv_{name}_code")
        print(f"compiled {name} in {(time.time()-conv_start)*1000:.2f}ms")
        
        run_start = time.time()
        output = getattr(compiled_module, name)(*args, **kwargs)
        print(f"ran {name} in {(time.time()-run_start)*1000:.2f}ms")
        
        return output

    return wrapper
