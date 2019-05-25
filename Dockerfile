FROM python:3.6

ARG project_dir=/app/

ADD bot.py ../gcp/Private.json $project_dir

WORKDIR $project_dir

RUN pip install flask google-cloud-language line-bot-sdk google-cloud-datastore numpy

EXPOSE 5000
CMD ["python", "bot.py"]
