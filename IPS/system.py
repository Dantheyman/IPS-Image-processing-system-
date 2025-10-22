import db

class System:
    def __init__(self):
        
        self.loaded_dataset = None
        self.loaded_model = None
        self.display = None
        self.process_going = False

    def change_dataset(self,id):
        
        self.loaded_dataset = Dataset(id)

    
       

class Dataset:
    def  __init__(self, id,):
        self.id = id
       
        db.load_dataset(id)  
     
            

#singleton Instance of system class
system_instance = System()




    
        