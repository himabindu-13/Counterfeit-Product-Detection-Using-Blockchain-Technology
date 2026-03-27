from web3 import Web3
import json
import hashlib

class Blockchain:
    def __init__(self):
        # Connect to Ganache
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        
        # Simple product registry contract ABI
        self.contract_abi = [
            {
                "inputs": [],
                "stateMutability": "nonpayable",
                "type": "constructor"
            },
            {
                "anonymous": False,
                "inputs": [
                    {
                        "indexed": True,
                        "internalType": "bytes32",
                        "name": "productHash",
                        "type": "bytes32"
                    },
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "manufacturer",
                        "type": "address"
                    }
                ],
                "name": "ProductRegistered",
                "type": "event"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "productHash",
                        "type": "bytes32"
                    }
                ],
                "name": "getProduct",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "manufacturer",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "isVerified",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "productHash",
                        "type": "bytes32"
                    }
                ],
                "name": "registerProduct",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {
                        "internalType": "bytes32",
                        "name": "",
                        "type": "bytes32"
                    }
                ],
                "name": "products",
                "outputs": [
                    {
                        "internalType": "address",
                        "name": "manufacturer",
                        "type": "address"
                    },
                    {
                        "internalType": "uint256",
                        "name": "timestamp",
                        "type": "uint256"
                    },
                    {
                        "internalType": "bool",
                        "name": "isVerified",
                        "type": "bool"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        # Deploy contract (you'll need to replace with your deployed contract address)
        self.contract_address = '0x54F801a2dd2c62E84B0fAbccE12debC498590C1f'
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )
    
    def generate_product_hash(self, product_data):
        """Generate unique hash for product"""
        data_string = f"{product_data['name']}{product_data['batch_number']}{product_data['manufacturing_date']}"
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    def register_product(self, product_data, private_key):
        """Register product on blockchain"""
        product_hash = self.generate_product_hash(product_data)
        
        # Convert to bytes32
        product_hash_bytes = self.w3.toBytes(hexstr=product_hash)
        
        # Create transaction
        transaction = self.contract.functions.registerProduct(product_hash_bytes).buildTransaction({
            'from': self.w3.eth.accounts[0],
            'nonce': self.w3.eth.getTransactionCount(self.w3.eth.accounts[0]),
            'gas': 2000000,
            'gasPrice': self.w3.toWei('50', 'gwei')
        })
        
        # Sign transaction
        signed_txn = self.w3.eth.account.signTransaction(transaction, private_key=private_key)
        
        # Send transaction
        tx_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        
        return tx_hash.hex(), product_hash
    
    def verify_product(self, product_hash):
        """Verify product on blockchain"""
        try:
            product_hash_bytes = self.w3.toBytes(hexstr=product_hash)
            product_info = self.contract.functions.getProduct(product_hash_bytes).call()
            return {
                'manufacturer': product_info[0],
                'timestamp': product_info[1],
                'isVerified': product_info[2]
            }
        except:
            return None
