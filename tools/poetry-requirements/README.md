```sh
docker build -t poetry-requirements tools/poetry-requirements/
docker create --name=poetry-requirements poetry-requirements
docker cp poetry-requirements:/poetry-requirements.txt ./
docker rm poetry-requirements
```
