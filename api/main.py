from fastapi import FastAPI, HTTPException, Depends


app = FastAPI()

@app.get("/recommendations")
def get_recommendations(user_id: int, returnMetadata: bool=False):
    return {'items': [
        {'id': 74510},
        {'id': 76157},
    ]}
