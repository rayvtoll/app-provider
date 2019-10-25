FROM python:3.7-alpine
RUN apk add -U docker jq
RUN pip3 install --upgrade pip && pip3 install flask
WORKDIR /app
COPY chrome.json /app
COPY api.py /app
EXPOSE 80
ENTRYPOINT ["python3"]
CMD ["api.py"]
