from streamlit.testing.v1 import AppTest
import traceback

at = AppTest.from_file("app.py")
at.run(timeout=15)

if at.exception:
    print("=== EXCEPTION ===")
    print(at.exception[0])
    print("Type:", type(at.exception[0]))
    try:
        print(at.exception[0].message)
    except:
        pass
    print("=================")
else:
    print("=== NO EXCEPTION ===")
