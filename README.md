# Cattle-cloud


> [!NOTE]
> This is the helper repo for the [Indian Bovine Breeds Kaggle dataset](https://www.kaggle.com/datasets/lukex9442/indian-bovine-breeds).

Minimal Quick Start: Clone, Install, and Run the Keras-Based Identification Script.
<br/>

### 1. Clone the repository


```bash
git clone https://github.com/pronoym99/Cattle-cloud.git
cd Cattle-cloud
```

### 2. (Optional) Create and activate a virtual environment


#### Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install required packages

```bash
pip install --upgrade pip
pip install tensorflow pillow numpy sqlalchemy
```

### 4. Run the identification script

```bash

# Run from the repository root:
python identification.py
```

This will:
- Load the Keras model from [models/cattle_identification_keras_model.h5](models/cattle_identification_keras_model.h5)
- Use the sample image at [assets/Indian_bovine_breeds/Hallikar/Hallikar_4.jpg](assets/Indian_bovine_breeds/Hallikar/Hallikar_4.jpg)
- Print the detected class (e.g., `Class detected: <BreedName>`)

### 5. Use your own image

Edit the image path in [identification.py](identification.py):

```python
# In identification.py
from PIL import Image
image = Image.open("path/to/your/image.jpg")
```

Keep the preprocessing (224x224) unchanged.

---

### Database ER Diagram

```mermaid
erDiagram
    USER {
        int userid PK
        int phone
        string address
    }

    LIVESTOCK {
        int livestockid PK
        string address
    }

    REGISTRATION {
        int regid PK
        int userid FK
        int livestockid FK
    }

    TRANSACTIONS {
        int txnid PK
        string txntime
        bool txnstatus
        int regid FK
        int seller_id FK
        int customer_id FK
        int livestock_id FK
    }

    TRANSPORTATION {
        int event_id PK
        int livestock_id FK
        int transporter_user_id FK
        string destination_address
        string transported_at
    }

    USER ||--o{ REGISTRATION : "owns"
    LIVESTOCK ||--o{ REGISTRATION : "registered via"
    REGISTRATION ||--o{ TRANSACTIONS : "referenced in"
    USER ||--o{ TRANSACTIONS : "sells"
    USER ||--o{ TRANSACTIONS : "buys"
    LIVESTOCK ||--o{ TRANSACTIONS : "transferred in"
    LIVESTOCK ||--o{ TRANSPORTATION : "transported in"
    USER ||--o{ TRANSPORTATION : "transports"
```
