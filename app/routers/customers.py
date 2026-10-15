from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_customer
from app.models import Customer, Address
from app.schemas import CustomerOut, CustomerPatch, AddressInput, AddressPatch, AddressOut
router=APIRouter(prefix="/api/v1/customers",tags=["Customers"])
@router.get("/me",response_model=CustomerOut,summary="Get your profile",responses={401:{"description":"Authentication required"}})
def me(c:Customer=Depends(get_current_customer)):return c
@router.patch("/me",response_model=CustomerOut,summary="Update your profile",responses={401:{"description":"Authentication required"}})
def patch_me(data:CustomerPatch,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    for k,v in data.model_dump(exclude_unset=True).items():setattr(c,k,v)
    db.commit();db.refresh(c);return c
@router.get("/{customer_id}",response_model=CustomerOut,summary="Get a customer profile",responses={401:{"description":"Authentication required"},403:{"description":"Customers may only access their own profile"}})
def get_customer(customer_id:int,c:Customer=Depends(get_current_customer)):
    if c.id!=customer_id:raise HTTPException(403,"Access denied")
    return c
@router.get("/me/addresses",response_model=list[AddressOut],summary="List your addresses")
def addresses(db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):return db.query(Address).filter_by(customer_id=c.id).order_by(Address.id).all()
@router.post("/me/addresses",response_model=AddressOut,status_code=201,summary="Add an address")
def add_address(data:AddressInput,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    if data.is_default:db.query(Address).filter_by(customer_id=c.id).update({"is_default":False})
    row=Address(customer_id=c.id,**data.model_dump());db.add(row);db.commit();db.refresh(row);return row
def owned_address(address_id:int,db:Session,c:Customer):
    row=db.get(Address,address_id)
    if not row:raise HTTPException(404,"Address not found")
    if row.customer_id!=c.id:raise HTTPException(403,"Access denied")
    return row
@router.patch("/me/addresses/{address_id}",response_model=AddressOut,summary="Update one of your addresses",responses={403:{"description":"Access denied"},404:{"description":"Address not found"}})
def patch_address(address_id:int,data:AddressPatch,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    row=owned_address(address_id,db,c)
    changes=data.model_dump(exclude_unset=True)
    if changes.get("is_default"):db.query(Address).filter(Address.customer_id==c.id,Address.id!=row.id).update({"is_default":False})
    for k,v in changes.items():setattr(row,k,v)
    db.commit();db.refresh(row);return row
@router.delete("/me/addresses/{address_id}",status_code=204,summary="Delete one of your addresses",responses={403:{"description":"Access denied"},404:{"description":"Address not found"}})
def delete_address(address_id:int,db:Session=Depends(get_db),c:Customer=Depends(get_current_customer)):
    db.delete(owned_address(address_id,db,c));db.commit();return Response(status_code=204)
