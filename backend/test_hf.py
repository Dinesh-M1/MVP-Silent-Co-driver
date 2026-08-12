from app.main import predict
from app.schemas import DriverInput

if __name__ == "__main__":
    payload = DriverInput(transcript="I feel tired and stressed after a long drive", context="highway")
    print(predict(payload))
