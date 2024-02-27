import torch
from transformers import pipeline
import pandas as pd
#import os
from datasets import Dataset, DatasetDict
import datasets
from transformers.pipelines.pt_utils import KeyDataset
from tqdm.auto import tqdm
import logging
import warnings
from io import BytesIO
from google.oauth2 import service_account
from google.cloud import storage

warnings.filterwarnings("ignore", message="Length of IterableDataset.*")

device = "cuda:0" if torch.cuda.is_available() else "cpu"

train_df = pd.DataFrame(columns = ["cont", "audio", "Resultado"])

google_credentials = service_account.Credentials.from_service_account_file("whisper-coes-2d46b1614374.json")
storage_client = storage.Client(credentials = google_credentials)

transcribe = pipeline(
                      task            = "automatic-speech-recognition",
                      model           = "model/",
                      chunk_length_s  = 30,
                      device          = device
                      )
transcribe.model.config.forced_decoder_ids = transcribe.tokenizer.get_decoder_prompt_ids(language="es", task="transcribe")
blobs = storage_client.list_blobs("coes-bucket")
cont = 0
print("Antes del Bucle")
#print(transcribe("audioprueba.opus")["text"])

for blob in blobs:
  if blob.name.endswith(".opus"):
    print(blob.name)
    train_df = pd.concat([train_df, pd.DataFrame({'cont': [cont], 'audio': [blob.name]})], ignore_index=True)
    audio_data = blob.download_as_string()
    #train_df.loc[cont, "Resultado"] = transcribe(audio_data)["text"]
    cont = cont + 1
  elif blob.name == "prueba_whisper.xlsx":
    bucket = storage_client.bucket("coes-bucket")
    blob = bucket.blob("prueba_whisper.xlsx")
    generation_match_precondition = 0
    blob.reload()
    generation_match_precondition = blob.generation
    blob.delete(if_generation_match=generation_match_precondition)
    
print("Termino el Bucle")
excel_buffer = BytesIO()
train_df.to_excel(excel_buffer, index=False)
excel_buffer.seek(0) 
print("Crea excel")

bucket = storage_client.bucket("coes-bucket")
blob = bucket.blob("prueba_whisper.xlsx")
generation_match_precondition = 0
 
blob.upload_from_file(excel_buffer,
                      if_generation_match = generation_match_precondition,
                      content_type        = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                     )
#    print(train_df)
warnings.resetwarnings()


from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '¡Hola, mundo! Esta es una aplicación web desplegada en Cloud Run. Despliegue Total'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8501)

#def main():
#  return{
#    "statusCode":200,
#    "Body": "Hello"
#  }
#
#if __name__ == "__main__":
#    main()
