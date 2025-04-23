import threading
from motor_one_code import motor_one_main
from motor_two_code_old import motor_two_main
from motor_controller_old import DualMotorController
from speedControllerDummy import DualMotorSpeedController
import time


def main():
    # Shared instances
    shared_controller = DualMotorController("COM5", 9600)
    shared_speed_controller = DualMotorSpeedController()

    try:
        # Create and start threads
        t1 = threading.Thread(target=motor_one_main, args=(shared_controller, shared_speed_controller))


        t1.start()
        time.sleep(2)
        t2 = threading.Thread(target=motor_two_main, args=(shared_controller, shared_speed_controller))
        t2.start()

        t1.join()
        t2.join()

    except KeyboardInterrupt:
        shared_controller.set_speeds(0, 0)  # Stop both motors
        shared_controller.close()
        print("System shutdown complete")


if __name__ == "__main__":
    main()