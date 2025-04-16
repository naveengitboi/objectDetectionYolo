# singleton.py
import commonData


class _GlobalState:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.data_store = commonData.DataHouse()
        return cls._instance


# Create singleton instance
GLOBAL_STATE = _GlobalState()


def get_data_store():
    return GLOBAL_STATE.data_store