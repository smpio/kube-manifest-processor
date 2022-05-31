FROM python:3.9
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .

ENTRYPOINT ["python", "-m", "kube_manifest_processor"]
