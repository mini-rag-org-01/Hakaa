
## Requirements

- fastapi 0.121.1
- uvicorn 0.38.0
- python-multipart 0.0.20
- python-dotenv 1.2.1
- pydantic-settings 2.12.0

#### Install Dependencies

```bash
sudo apt update
sudo apt install libpq-dev gcc python3-dev
```

#### Install Python using MiniConda

1) Download and install MiniConda from [here](https://docs.anaconda.com/free/miniconda/#quick-command-line-install)
2) Create a new environment using the following command:
```bash
$ conda create -n mini-rag python=3.10
```
3) Activate the environment:
```bash
$ conda activate mini-rag
```
### (Optional) Setup you command line interface for better readability

```bash
export PS1="\[\033[01;32m\]\u@\h:\w\n\[\033[00m\]\$ "
```


## Installation

### Install the required packages
```bash
$ pip install -r requirements.txt
```

### Setup the environment variables
```bash
$ cp .env.example .env
```


### Run the fast api server
```bash
$ uvicorn main:app --reload --host 0.0.0.0 --port 5000
```
