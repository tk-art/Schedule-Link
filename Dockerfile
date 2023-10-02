FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/

RUN python -m venv /venv
ENV PATH="/venv/bin:$PATH"
RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install -r requirements.txt
RUN pip install pillow
COPY . /code/
