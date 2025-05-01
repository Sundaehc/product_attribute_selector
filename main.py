from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn

from attribute_selector import AttributeSelector

# Define the request model
class AttributeSelectionRequest(BaseModel):
    product_number: str
    attribute_name: str
    available_values: List[str]
    image_path: Optional[str] = None

# Define the response model
class AttributeSelectionResponse(BaseModel):
    product_number: str
    selected_value: str

# Create FastAPI app
app = FastAPI(
    title="Product Attribute Selection Service",
    description="Service for selecting appropriate attribute values for products",
    version="1.0.0"
)

@app.post("/select-attribute", response_model=AttributeSelectionResponse)
async def select_attribute(request: AttributeSelectionRequest):
    """
    Select an appropriate attribute value for a product.
    
    Args:
        request: AttributeSelectionRequest containing product details
        
    Returns:
        AttributeSelectionResponse with selected attribute value
    """
    try:
        selector = AttributeSelector()
        result = selector.select_attribute_value(
            request.product_number,
            request.attribute_name,
            request.available_values,
            request.image_path
        )
        
        return AttributeSelectionResponse(
            product_number=result[0],
            selected_value=result[1]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing attribute selection: {str(e)}"
        )

def main():
    """Main function to run the FastAPI server"""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=14736,
        log_level="info"
    )

if __name__ == "__main__":
    main()
