
#     Explaining Data Science Concepts with Gemma

<p align="center"> 
<img src="https://i.ibb.co/J7291t1/kaggle-9.png" alt="kaggle-9" border="0">
</p>

[![Gemma](https://img.shields.io/badge/Gemma-gemma_2b_en-%233582ff?style=flat&label=Gemma&labelColor=%231a2331)](https://blog.google/technology/developers/gemma-open-models/)
[![Keras](https://img.shields.io/badge/Keras%20NLP-Gemma-%231a2331?labelColor=%23f32424
)](https://keras.io/api/keras_nlp/models/gemma/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-BAAI%2Fbge%20base%20en%20v1.5-%23000000?style=flat&labelColor=%23ffd21f)](https://huggingface.co/BAAI/bge-base-en-v1.5)
[![LlamaIndex](https://img.shields.io/badge/LlamaIndex-RAG-%23fac5ee?style=flat&labelColor=%2385e4f8)](https://docs.llamaindex.ai/en/stable/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-%238cf1ff?style=flat&labelColor=%2301004b)](https://www.pinecone.io/)


This notebook aims to **Explain or Teach Basic Data Science Concepts with Gemma**.

**Gemma** is a family of lightweight, state-of-the-art open models built from the same research and technology used to create the Gemini models. Developed by Google DeepMind and other teams across Google, Gemma is inspired by Gemini, and the name reflects the Latin gemma, meaning “precious stone.”

The notebook starts with a baseline, and methodically develops the model step-by-step to cultivate a more accurate and robust version.

In this notebook, we delve into diverse methodologies to employ Gemma for elucidating data science concepts. Our exploration encompasses three strategies: *Untuned Model*, *Custom Fine-tuning*, and a synthesis of *RAG with Fine-tuning*. We will illustrate these strategies through the following detailed approaches:

1. **Untuned Gemma (`gemma_2b_en`)**: Employing the baseline, untuned version of Gemma, we assess its efficacy in elucidating data science concepts.
2. **Fine-Tuning with Custom Dataset**: We will fine-tune the base Gemma (`gemma_2b_en`) model using a specially curated dataset on data science concepts. The dataset, titled "*1000+ Data Science Concepts*," is available [here](https://www.kaggle.com/datasets/hserdaraltan/1000-data-science-concepts) and is also provided as a CSV file in the GitHub folder.
3. **RAG with Gemma (`gemma_2b_en`) and LlamaIndex**: Utilizing Wikipedia as a data source, this configuration employs the fine-tuned Gemma model to combine and output responses from these sources effectively. We use **Pinecone** to create an index and vector store that organizes documents into chunks for efficient search and retrieval. This methodology is detailed further in the blog titled ["Google — AI Assistants for Data Tasks with Gemma"](https://towardsdev.com/google-ai-assistants-for-data-tasks-with-gemma-8aac607c032a) on [Towards Dev](https://towardsdev.com/).

We will ultimately evaluate the results produced by these three methodologies, and compare how each explains a particular data science concept.

The notebook can also be found on Kaggle as ["Data Science with Gemma, LlamaIndex, and Pinecone"](https://www.kaggle.com/code/hserdaraltan/data-science-with-gemma-llamaindex-and-pinecone).
