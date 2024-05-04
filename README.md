# AI Assistant for Engineering Tools Onboarding

This repo is the complete code for article [SaaS-based Engineering Tool Onboarding with AI Assistance](https://medium.com/towards-artificial-intelligence/saas-based-engineering-tool-onboarding-with-ai-assistance-c34c533224a7).

This prototype application uses dummy data and partial official SaaS platform documentation and downloaded public PDFs as source of knowledge base for demo purposes.

## Demo

https://github.com/sparkwithdots/engineering-tools-onboarding/assets/153865750/b426f3be-d35e-4517-b93f-aae977b9a2d2

## Prepare environment

The prototype application is implemented in Python, it uses conda as the package and environment management tool. You can refer [this doc](https://conda.io/projects/conda/en/latest/user-guide/install/index.html) to install conda.

Once you get conda installed, run below commands from terminal to get environment ready.
```
$ conda create --name engineering-tools-onboarding python=3.10

$ conda activate engineering-tools-onboarding

$ pip install -r requirements.txt
```

Next you need to copy the file `application.env.example` to `application.env`, provide your own [OpenAI API key](https://platform.openai.com/docs/quickstart/step-2-set-up-your-api-key) and [Tavily API key](https://docs.tavily.com/docs/tavily-api/introduction) to fill the environment variables in `application.env` file.

## Prepare data

The data is to setup the dummy learning objects and RAG documents to persist for each service. You need to create a `data` folder if it doesn't exist under the project root folder. All the data will be located under this folder.

Under the project root folder, run below python file to prepare all the data.
```
$ python prepare_data.py
```

Once it is done, you will expect to see `learning_objects_with_embedding.csv` file, `docstore` and `vectorstore` folders with data collections for each service (github, launchdarkly and snyk).

## Run application

Under the project root folder, you can run the application as command below.
```
$ streamlit run main.py

# If you want to disable gathering usage stats from the browser, run

$ streamlit run main.py --browser.gatherUsageStats false
```
The application will listen to `8501` port by default, and you can open the URL from your browser.

