from pymongo import MongoClient

#подключаемся к MongoDB (пока локально)
client = MongoClient("localhost", 27017)

#создаем базу данных
db = client['almost_notion']

#создаем коллекции
todo_collection = db['todo_list']
kanban_collection = db['kanban_board']
note_collection = db['notes']




