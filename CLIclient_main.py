import asyncio
import websockets
from cryptography.hazmat.primitives import serialization as s
from client_modules import encryption as e
from client_modules import packet_handler as p
from uuid import uuid4
import pickle
from sys import exit

async def send_message(websocket, message):
    outpacket = e.encrypt_packet(
        message, SERVER_CREDS['server_epbkey']
    )
    await websocket.send(outpacket)
    response = await websocket.recv()
    return await handle_resp(websocket, response)

async def handle_resp(websocket, response):
    inpacket = e.decrypt_packet(response, CLIENT_CREDS['client_eprkey'])
    print(inpacket)
    handled = await p.handle(SERVER_CREDS, CLIENT_CREDS, websocket, inpacket) # handle here using type and data
    print('resposne handaled')
    return handled

async def main():
    host = input("Enter hostname of server: ")
    port = int(input("Enter port: "))
    uri = f"ws://{host}:{port}"
    async with websockets.connect(uri, ping_interval=30) as websocket:
        con_id = str(uuid4())
        await websocket.send(pickle.dumps({'type':'CONN_INIT', 'data':con_id}))
        try:
            key = await websocket.recv()
            key = pickle.loads(key)
            pubkey = s.load_pem_public_key(key['data'])
            SERVER_CREDS['server_epbkey'] = pubkey
            print("RECEIVED SERVER PUBLIC KEY")
            await websocket.send(pickle.dumps({'type':'CONN_ENCRYPT_C','data':CLIENT_CREDS['client_epbkey']}))
            print(e.decrypt_packet(await websocket.recv(), CLIENT_CREDS['client_eprkey']))

        except websockets.exceptions.ConnectionClosedError as err:
            print("Disconected from Server! Error:\n",err)
            exit()
        
        while True:
            type = input('Enter Packet Type: ')
            data = eval(input("Enter Packet Data: "))
            print(await send_message(websocket, {'type':type, 'data':data}))


SERVER_CREDS = {}
CLIENT_CREDS = {}

if __name__ == '__main__':
    client_eprkey, client_epbkey = e.create_conn_key_pair()
    CLIENT_CREDS['client_eprkey'] = client_eprkey
    CLIENT_CREDS['client_epbkey'] = e.ser_key_pem(client_epbkey, 'public')
    asyncio.get_event_loop().run_until_complete(main())
    asyncio.get_event_loop().run_forever()

"""
import asyncio
import websockets

# Define the server URI
uri = "ws://localhost:8765"

# Function to handle incoming messages from the server
async def handle_incoming_messages(websocket):
    async for message in websocket:
        # Handle the message here
        print(f"Received message: {message}")

# Function to handle outgoing messages to the server
async def handle_outgoing_messages(websocket):
    while True:
        message = await asyncio.get_event_loop().run_in_executor(None, input, "Enter a message: ")
        await websocket.send(message)

# Main function to connect to the server and start the message handlers
async def main():
    async with websockets.connect(uri) as websocket:
        # Start the message handlers
        await asyncio.gather(
            handle_incoming_messages(websocket),
            handle_outgoing_messages(websocket),
        )

# Run the main function
asyncio.run(main())
"""