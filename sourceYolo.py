import os

folderName = "C:/Users/Nandini/OneDrive/Desktop/artworks"
print(os.getcwd())
os.chdir(folderName)

print(os.getcwd())
def renamingFiles():
    cnt = 0
    for item in os.listdir():
        name = os.path.join(folderName,item)
        newfileName = str(cnt) + ".jpg"
        if os.path.isfile(name):
            os.rename(item, newfileName)
            cnt+=1
