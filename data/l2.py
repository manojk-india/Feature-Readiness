import pandas as pd
import random
from random import randint
from datetime import datetime,timedelta

boards=["APS","DIS","TES"]

features = {
    "DIS-1":"RTB","DIS-2":"CTB","DIS-3":"RTB","DIS-4":"CTB",
    "DIS-5":"RTB","DIS-6":"CTB","DIS-7":"RTB",
    "TES-1":"CTB","TES-2":"RTB",
    "TES-3":"RTB","TES-4":"CTB",
    "APS-1":"CTB","APS-2":"RTB",
    "APS-3":"RTB","APS-4":"CTB"
}

parent_links=["parent_link_1","parent_link_2","parent_link_3","parent_link_4","parent_link_5"]
boards=["CDF","EBSNF","TES1","TES2","APS1","APS2"]


data=[]
for i in features.keys():
    random_days=random.randint(0,60)
    board=i[0:3]
    data.append({
        "key":i,
        "board":board,
        "summary":f"TASK {i[4]} for {board}",
        "description":f"Description for feature {i[4]} for {board}",
        "acceptance_criteria":f"Acceptance criteria for feature {i[4]} for {board}",
        "labels":features[i],
        "components":random.choice(boards),
        "parent_link":random.choice(parent_links),
        "requested_by":features[i],
        "estimate":random.randint(10,40),
        "due_date": datetime(2025,4,24)+timedelta(random_days)
    })

df=pd.DataFrame(data)
df.to_csv("data/l2_board.csv",index=False)