FROM golang:1.21

WORKDIR /app

COPY go.mod ./
RUN go mod download

COPY . .

RUN go build -o app .

RUN useradd -u 1001 -m appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["./app"]
