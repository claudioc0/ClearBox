FROM python:3.9-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./nltk.txt /code/nltk.txt

RUN pip install --no-cache-dir -r requirements.txt

RUN python -m nltk.downloader -d /usr/share/nltk_data -r /code/nltk.txt

COPY ./backend /code/backend
COPY ./static /code/static

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "backend.app:app"]