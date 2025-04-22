import threading
import motorTwoCode
import mainCode2
from dual_motor_arduino import DualMotorController


def loop():
    # Single shared controller instance
    shared_controller = DualMotorController('COM5')

    try:
        # Create threads
        t1 = threading.Thread(target=mainCode2.main())
        t2 = threading.Thread(target=motorTwoCode.main())

        # Start threads
        t1.start()
        t2.start()

        # Wait for completion
        t1.join()
        t2.join()

    except KeyboardInterrupt:
        shared_controller.set_speeds(0, 0)  # Stop both motors
        shared_controller.close()


loop()