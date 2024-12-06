#import starlette.status as status
#from fastapi import APIRouter, Form
#from fastapi.responses import RedirectResponse
#from fastapi.templating import Jinja2Templates

#from database import *
#
#templates = Jinja2Templates(directory="templates")

#router = APIRouter(
#    prefix="/profile",
#    tags=["Profile"]
#)

#@router.post("/main_page/profile/{user_id}")
#async def profile_page(user_id : int, first_name = Form(), last_name = Form(), age = Form()) :
#    user_dict = {"user_id" : user_id, "first_name" : first_name, "last_name" : last_name, "age" : age}
#    await add_profile_data(**user_dict)
#    return RedirectResponse("/main_page/profile" + str(user_id),
#                            status_code=status.HTTP_302_FOUND)