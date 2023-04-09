import socket
import pickle
import os
import re
import time
import struct
import json
import requests
import _thread
import rsa
public_key,private_key=rsa.newkeys(2048)
encoded_public_key=pickle.dumps(public_key)
encoded_public_key_len=struct.pack('L',len(encoded_public_key))
with open('names.json','r') as f:
  names=json.load(f)
with open('passwords.json','r') as f:
  passwords=json.load(f)
chat_messages=[['system',"Hello_world!"],]
s=socket.socket(socket.AF_INET6,socket.SOCK_STREAM)
s.bind((input('IPv6_address:'),1024))
s.listen(1000)
s1=socket.socket()
s1.bind(('127.0.0.1',2048))
s1.listen(100)
def split(long_message,public_key):
  sec=100
  messages=[long_message[i:i+sec] for i in range(0,len(long_message),sec)]
  encoded_messages=[]
  for i in messages:
    encoded_messages.append(rsa.encrypt(i,public_key))
  encoded_messages=pickle.dumps(encoded_messages)
  encoded_messages_len=struct.pack('L',len(encoded_messages))
  return [encoded_messages_len,encoded_messages]
def client(s):
  global names
  global passwords
  while True:
    c,addr=s.accept()
    print(addr)
    print('accept')
    lenth=struct.unpack('L',c.recv(4))[0]
    con=c.recv(lenth).decode()
    if con=='name_test':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      if name in names:
        c.send('T'.encode())
        c.close()
      else:
        c.send('F'.encode())
        c.close()
    elif con=='sign_up':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_lenth=struct.unpack('L',c.recv(4))[0]
      key=c.recv(key_lenth).decode()
      c.close()
      names.append(name)
      passwords[name]=key
      with open('names.json','w') as f:
        json.dump(names,f)
      with open('passwords.json','w') as f:
        json.dump(passwords,f)
      os.mkdir('files\\'+name)
    elif con=='login_in':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_lenth=struct.unpack('L',c.recv(4))[0]
      key=c.recv(key_lenth).decode()
      if name not in names:
        c.send('F')
        c.close()
        continue
      if passwords[name]==key:
        c.send('T'.encode())
        c.close()
      else:
        c.send('F'.encode())
        c.close()
    elif con=='file_send':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_lenth=struct.unpack('L',c.recv(4))[0]
      key=c.recv(key_lenth).decode()
      file_name_lenth=struct.unpack('L',c.recv(4))[0]
      file_name=c.recv(file_name_lenth).decode()
      if name not in names:
        c.send('F')
        c.close()
        continue
      if passwords[name]==key:
        c.send('T'.encode())
        file_piece_num=struct.unpack('L',c.recv(4))[0]
        with open('files\\'+name+'\\'+file_name,'bw') as f:
          for i in range(file_piece_num+1):
            lenth=struct.unpack('L',c.recv(4))[0]
            print(addr,':',lenth)
            piece=c.recv(lenth)
            f.write(piece)
            f.flush()
            c.send('V'.encode())
        c.close()
      else:
        c.send('F'.encode())
        c.close()
    elif con=='file_get':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_lenth=struct.unpack('L',c.recv(4))[0]
      key=c.recv(key_lenth).decode()
      if name not in names:
        c.send('F')
        c.close()
        continue
      if passwords[name]==key:
        c.send('T'.encode())
        author_name_lenth=struct.unpack('L',c.recv(4))[0]
        author_name=c.recv(author_name_lenth).decode()
        file_name_lenth=struct.unpack('L',c.recv(4))[0]
        file_name=c.recv(file_name_lenth).decode()
        if os.path.exists('files\\'+author_name+'\\'+file_name):
          c.send('T'.encode())
          file_size=os.path.getsize('files\\'+author_name+'\\'+file_name)
          size=piece_size=1024*400
          num=piece_num=file_size//piece_size
          if file_size%piece_size>0:
            #piece_num+=1
            end_size=file_size%piece_size
          else:
            piece_num-=1
            num-=1
            end_size=piece_size
          end_size=struct.pack('L',end_size)
          piece_num=struct.pack('L',piece_num)
          piece_size=struct.pack('L',piece_size)
          c.send(piece_num)
          with open('files\\'+author_name+'\\'+file_name,'br') as f:
            for i in range(num):
              piece=f.read(size)
              c.send(piece_size)
              c.send(piece)
              c.recv(1)
              #print(i)
            piece=f.read(size)
            c.send(end_size)
            c.send(piece)
            c.recv(1)
            #print('end')
          c.close()
        else:
          c.send('F'.encode())
          c.close()
        #c.close()
      else:
        c.send('F'.encode())
        c.close()
    elif con=='send_message':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_password_len=struct.unpack('L',c.recv(4))[0]
      key_password=c.recv(key_password_len).decode()
      if name not in names:
        c.send('F')
        c.close()
        continue
      if passwords[name]==key_password:
        c.send('T'.encode())
        c.send(encoded_public_key_len)
        c.send(encoded_public_key)
        message_len=struct.unpack('L',c.recv(4))[0]
        message=c.recv(message_len)
        c.close()
        message=rsa.decrypt(message,private_key)
        message=pickle.loads(message)
        print(message)
        chat_messages.append(message)
      else:
        c.send('F'.encode())
        c.close()
    elif con=='get_message':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_password_len=struct.unpack('L',c.recv(4))[0]
      key_password=c.recv(key_password_len).decode()
      if name not in names:
        c.send('F')
        c.close()
        continue
      if passwords[name]==key_password:
        c.send('T'.encode())
        client_public_key_len=struct.unpack('L',c.recv(4))[0]
        client_public_key=pickle.loads(c.recv(client_public_key_len))
        end_num=int(struct.unpack('f',c.recv(4))[0])
        new_end_num=float(len(chat_messages)-1)
        if end_num==0:
          if len(chat_messages)<=1:
            return_list=[]
          else:
            return_list=[chat_messages[0],chat_messages[-1]]
        else:
          return_list=chat_messages[end_num:]
          del return_list[0]
        new_end_num=struct.pack('f',new_end_num)
        return_list=pickle.dumps(return_list)
        return_list_len,return_list=split(return_list,client_public_key)
        c.send(return_list_len)
        c.send(return_list)
        c.send(new_end_num)
        c.close()
      else:
        c.send('F'.encode())
        c.close()
    elif con=='chat_exit':
      name_len=struct.unpack('L',c.recv(4))[0]
      name=c.recv(name_len).decode()
      key_password_len=struct.unpack('L',c.recv(4))[0]
      key_password=c.recv(key_password_len).decode()
      if name not in names:
        c.send('F')
        c.close()
        continue
      if passwords[name]==key_password:
        c.send('T'.encode())
        c.close()
        chat_messages.append(['system',name+' escaped'])
        print(str(['system',name+' escaped']))
      else:
        c.send('F'.encode())
        c.close()
    else:
      c.close()
    print(addr,'over')
def sever(s):
  while True:
    try:
      client(s)
    except Exception as e:
      print(e)
a=_thread.start_new_thread(client,(s,))
b=_thread.start_new_thread(client,(s1,))
while True:pass
