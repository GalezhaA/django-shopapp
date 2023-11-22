FROM python:3.11

ENV PYTHONUNBUFERRED=1

WORKDIR /app

RUN pip install --upgrade pip "poetry==1.7.1"
RUN poetry config virtualenvs.create false --local
COPY pyproject.toml poetry.lock ./
RUN poetry install

COPY mysite .

CMD ["python", "manage.py", "runserver"]
