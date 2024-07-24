import threading
import os, sys, time

lock = threading.Lock()
count = 0
testfile = open('cringer.txt', 'w')

def writeThread():
    global count
    global testfile

    while True:
        with lock:
            testfile.write(str(count))
            count += 1
            print(f"count is {count} writing to {hex(id(testfile))}")
            time.sleep(.1)
            testfile.flush()

def renamer():
    global testfile
    global count

    while True: 
        if count == 10:
            with lock:
                print(f"renaming file at {hex(id(testfile))}")
                testfile.close()
                curdir = os.getcwd()
                oldfilepath = curdir + '/cringer.txt'
                newfilepath = curdir + '/cringiest.txt'
                print(f'old: {oldfilepath} new: {newfilepath}')
                os.system("cp " + oldfilepath + " " + newfilepath)
                #os.system("rm " + oldfilepath)
                testfile = open(newfilepath, 'a')
                print(f'done, new file at {hex(id(testfile))}')
        time.sleep(.1)
    
def main():
    global testfile
    print(f'testfile id: {hex(id(testfile))}')
    wr = threading.Thread(target=writeThread, name='writeThread')
    wr.start()
    rn = threading.Thread(target=renamer, name='renamer')
    rn.start()

if __name__ == '__main__':
    main()




