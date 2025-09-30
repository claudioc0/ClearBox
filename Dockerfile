FROM python:3.9-slim

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt
COPY ./nltk.txt /code/nltk.txt

RUN python -m nltk.downloader -d /usr/share/nltk_data punkt stopwords rslp punkt_tab

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . /code/

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "backend.app:app"]