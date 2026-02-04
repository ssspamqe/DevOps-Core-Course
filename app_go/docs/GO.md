# Go Language Justification

For the compiled language implementation, I chose **Go (Golang)**.

## Reasons for Choice

1.  **Performance**: Go is a compiled language that produces statically linked binaries. It generally offers better performance and lower footprint compared to interpreted languages like Python.
2.  **Concurrency**: Go's goroutines make it highly suitable for network services and concurrent processing, although for this simple app, it's overkill, it's a great feature for scaling.
3.  **Simplicity**: Go has a simple syntax and a strong standard library (`net/http`) that allows building robust web servers without any external dependencies.
4.  **Static Type System**: Go's type system helps catch errors at compile time, leading to more reliable code.
5.  **Single Binary Deployment**: The ability to compile everything into a single binary simplifies deployment (e.g., in Docker containers), as there's no need to manage a virtual environment or install dependencies on the target machine.

## Comparison with Python Version

| Feature | Python (Flask) | Go (net/http) |
| :--- | :--- | :--- |
| **Type** | Interpreted | Compiled |
| **Typing** | Dynamic | Static |
| **Startup Time** | Fast | Very Fast |
| **Deployment** | Requires Interpreter + Libs | Single Binary |
| **Developer Experience** | Rapid Prototyping | Robust Engineering |
