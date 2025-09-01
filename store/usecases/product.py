from decimal import Decimal
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID
from venv import logger
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import pymongo
from store.db.mongo import db_client
from store.models.product import ProductModel
from store.schemas.product import Decimal_, ProductIn, ProductOut, ProductUpdate, ProductUpdateOut, ProductFilters
from store.core.exceptions import InsertionException, NotFoundException

logger = logging.getLogger(__name__)

class ProductUsecase:
    def __init__(self) -> None:
        self.client: AsyncIOMotorClient = db_client.get()
        self.database: AsyncIOMotorDatabase = self.client.get_database()
        self.collection = self.database.get_collection("products")

    async def create(self, body: ProductIn) -> ProductOut:
        try:
            product_model = ProductModel(**body.model_dump())
            result = await self.collection.insert_one(product_model.model_dump())
            if result.inserted_id:
                return ProductOut(**product_model.model_dump(), id=str(result.inserted_id))
            else:
                raise InsertionException("Failed to create product: No inserted ID")
        except Exception as e:
            if 'result' in locals() and result.inserted_id:
                try:
                    await self.collection.delete_one({"_id": result.inserted_id})
                    logger.info(f"Rollback: Removed product {result.inserted_id}")
                except:
                    pass
            logger.error(f"Error inserting product: {str(e)}")
            raise InsertionException(f"Failed to create product: {str(e)}")

    async def get(self, id: UUID) -> ProductOut:
        result = await self.collection.find_one({"id": id})

        if not result:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        return ProductOut(**result)

    async def query(self, filters: Optional[ProductFilters] = None) -> List[ProductOut]:
        query_filter = {}
        
        if filters:
            if filters.min_price is not None:
                query_filter["price"] = {"$gte": float(filters.min_price)}
            if filters.max_price is not None:
                if "price" in query_filter:
                    query_filter["price"]["$lte"] = float(filters.max_price)
                else:
                    query_filter["price"] = {"$lte": float(filters.max_price)}
            
            if filters.name is not None:
                query_filter["name"] = {"$regex": filters.name, "$options": "i"}
                
            if filters.status is not None:
                query_filter["status"] = filters.status
            
        return [ProductOut(**item) async for item in self.collection.find(query_filter)]

    async def update(self, id: UUID, body: ProductUpdate) -> ProductUpdateOut:
        try:
            existing_product = await self.collection.find_one({"id": id})
            if not existing_product:
                raise NotFoundException(message=f"Product not found: {id}")
            update_data = body.model_dump(exclude_none=True)
            update_data['update_at'] = datetime.utcnow()
            
            if 'price' in update_data and update_data['price'] is not None:
                if isinstance(update_data['price'], Decimal):
                    update_data['price'] = float(update_data['price'])
                elif isinstance(update_data['price'], Decimal_):
                    update_data['price'] = float(update_data['price'].to_decimal())
            
            result = await self.collection.find_one_and_update(
                filter={"id": id},
                update={"$set": body.model_dump(exclude_none=True)},
                return_document=pymongo.ReturnDocument.AFTER,
            )
            
            if not result:
                raise InsertionException("Failed to update product")
            
            return ProductUpdateOut(**result)
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Erro updating product: {str(e)}")
            raise InsertionException(f"Failed to update product: {str(e)}")

    async def delete(self, id: UUID) -> bool:
        product = await self.collection.find_one({"id": id})
        if not product:
            raise NotFoundException(message=f"Product not found with filter: {id}")

        result = await self.collection.delete_one({"id": id})

        return True if result.deleted_count > 0 else False


product_usecase = ProductUsecase()
