# backend/monitor/drift_worker.py
from services.drift_service import DriftMonitor

def main():
    DriftMonitor().run_forever()

if __name__ == "__main__":
    main()
