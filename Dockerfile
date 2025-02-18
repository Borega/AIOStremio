FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache gcc python3-dev musl-dev linux-headers

RUN pip install --root-user-action ignore option uv

COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

COPY . .

EXPOSE 8469

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
