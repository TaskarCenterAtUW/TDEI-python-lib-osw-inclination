import os
import psutil
from src.config import Settings
from functools import lru_cache
from fastapi import FastAPI, APIRouter, Depends, status
from src.services.inclination_service import InclinationService

app = FastAPI()
app.incline_service = None

prefix_router = APIRouter(prefix='/health')


@lru_cache()
def get_settings():
    return Settings()


@app.on_event('startup')
async def startup_event(settings: Settings = Depends(get_settings)) -> None:
    try:
        print('<><> DL Directory <><>')
        config = Settings()
        print(config.get_download_directory())

        dl_directory = config.get_download_directory()
        if not os.path.exists(dl_directory):
            os.makedirs(dl_directory)
        app.incline_service = InclinationService()

    except Exception as e:
        print(e)
        print('\n\n\x1b[31m Application startup failed due to missing or invalid .env file \x1b[0m')
        print('\x1b[31m Please provide the valid .env file and .env file should contains following parameters\x1b[0m')
        print()
        print('\x1b[31m REQUEST_TOPIC=xxxx \x1b[0m')
        print('\x1b[31m REQUEST_SUBSCRIPTION=xxxx \x1b[0m')
        print('\x1b[31m RESPONSE_TOPIC=xxxx \x1b[0m')
        print('\x1b[31m QUEUECONNECTION=xxxx \x1b[0m')
        print('\x1b[31m STORAGECONNECTION=xxxx \x1b[0m \n\n')
        parent_pid = os.getpid()
        parent = psutil.Process(parent_pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()


@app.on_event('shutdown')
async def shutdown_event() -> None:
    print('Application is shutting down...')
    if app.incline_service:
        app.incline_service.stop_listening()


@app.get('/', status_code=status.HTTP_200_OK)
@prefix_router.get('/', status_code=status.HTTP_200_OK)
def root():
    Inclination().calculate()
    return "I'm healthy !!"


@app.get('/ping', status_code=status.HTTP_200_OK)
@app.post('/ping', status_code=status.HTTP_200_OK)
@prefix_router.get('/ping', status_code=status.HTTP_200_OK)
@prefix_router.post('/ping', status_code=status.HTTP_200_OK)
def ping():
    return "I'm healthy !!"


app.include_router(prefix_router)
