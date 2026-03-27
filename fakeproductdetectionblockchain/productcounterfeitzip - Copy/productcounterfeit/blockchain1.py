from web3 import Web3
import json
import hashlib
import os
from dotenv import load_dotenv

load_dotenv()

class Blockchain:
    def __init__(self):
        # Connect to Ganache
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:7545'))
        
        if not self.w3.is_connected():
            raise Exception("Failed to connect to Ganache")
        
        # Contract ABI and bytecode
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
                    },
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    },
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "batchNumber",
                        "type": "string"
                    }
                ],
                "name": "ProductRegistered",
                "type": "event"
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
                        "name": "fromAddress",
                        "type": "address"
                    },
                    {
                        "indexed": True,
                        "internalType": "address",
                        "name": "toAddress",
                        "type": "address"
                    },
                    {
                        "indexed": False,
                        "internalType": "string",
                        "name": "transactionType",
                        "type": "string"
                    }
                ],
                "name": "ProductTransferred",
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
                        "name": "exists",
                        "type": "bool"
                    },
                    {
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "batchNumber",
                        "type": "string"
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
                    },
                    {
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "batchNumber",
                        "type": "string"
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
                        "name": "productHash",
                        "type": "bytes32"
                    },
                    {
                        "internalType": "address",
                        "name": "toAddress",
                        "type": "address"
                    },
                    {
                        "internalType": "string",
                        "name": "transactionType",
                        "type": "string"
                    }
                ],
                "name": "transferProduct",
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
                        "name": "exists",
                        "type": "bool"
                    },
                    {
                        "internalType": "string",
                        "name": "productName",
                        "type": "string"
                    },
                    {
                        "internalType": "string",
                        "name": "batchNumber",
                        "type": "string"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        self.contract_bytecode = "0x608060405234801561001057600080fd5b50336000806101000a81548173ffffffffffffffffffffffffffffffffffffffff021916908373ffffffffffffffffffffffffffffffffffffffff1602179055506106c2806100606000396000f3fe608060405234801561001057600080fd5b506004361061007d5760003560e01c80638f887c2d1161005b5780638f887c2d146100f2578063b0f2f72a14610122578063d83ae6c714610152578063f8a8fd6d146101825761007d565b80631a5c6091146100825780634e04f5a3146100b25780637dc0d1d0146100d6575b600080fd5b61009c6004803603810190610097919061041c565b6101b2565b6040516100a99190610462565b60405180910390f35b6100ba6101ca565b6040516100cd97969594939291906104c8565b60405180910390f35b6100de61022a565b6040516100eb919061054a565b60405180910390f35b61010c60048036038101906101079190610565565b610250565b6040516101199190610462565b60405180910390f35b61013c600480360381019061013791906105c8565b610268565b6040516101499190610462565b60405180910390f35b61016c6004803603810190610167919061062b565b610280565b6040516101799190610462565b60405180910390f35b61019c60048036038101906101979190610658565b610298565b6040516101a99190610462565b60405180910390f35b60006020528060005260406000206000915090505481565b600080600080600080600080600080600054600154600254600354600454600554600654600754600854600954600a54600b54600c54600d54600e54600f54601054601154601254601354601454601554601654601754601854601954601a54601b54601c54601d54601e54601f54602054602154602254602354602454602554602654602754602854602954602a54602b54602c54602d54602e54602f54603054603154603254603354603454603554603654603754603854603954603a54603b54603c54603d54603e54603f54604054604154604254604354604454604554604654604754604854604954604a54604b54604c54604d54604e54604f54605054605154605254605354605454605554605654605754605854605954605a54605b54605c54605d54605e54605f54606054606154606254606354606454606554606654606754606854606954606a54606b54606c54606d54606e54606f54607054607154607254607354607454607554607654607754607854607954607a54607b54607c54607d54607e54607f54608054608154608254608354608454608554608654608754608854608954608a54608b54608c54608d54608e54608f54609054609154609254609354609454609554609654609754609854609954609a54609b54609c54609d54609e54609f5460a05460a15460a25460a35460a45460a55460a65460a75460a85460a95460aa5460ab5460ac5460ad5460ae5460af5460b05460b15460b25460b35460b45460b55460b65460b75460b85460b95460ba5460bb5460bc5460bd5460be5460bf5460c05460c15460c25460c35460c45460c55460c65460c75460c85460c95460ca5460cb5460cc5460cd5460ce5460cf5460d05460d15460d25460d35460d45460d55460d65460d75460d85460d95460da5460db5460dc5460dd5460de5460df5460e05460e15460e25460e35460e45460e55460e65460e75460e85460e95460ea5460eb5460ec5460ed5460ee5460ef5460f05460f15460f25460f35460f45460f55460f65460f75460f85460f95460fa5460fb5460fc5460fd5460fe5460ff546101005461010154610102546101035461010454610105546101065461010754610108546101095461010a5461010b5461010c5461010d5461010e5461010f546101105461011154610112546101135461011454610115546101165461011754610118546101195461011a5461011b5461011c5461011d5461011e5461011f546101205461012154610122546101235461012454610125546101265461012754610128546101295461012a5461012b5461012c5461012d5461012e5461012f546101305461013154610132546101335461013454610135546101365461013754610138546101395461013a5461013b5461013c5461013d5461013e5461013f546101405461014154610142546101435461014454610145546101465461014754610148546101495461014a5461014b5461014c5461014d5461014e5461014f546101505461015154610152546101535461015454610155546101565461015754610158546101595461015a5461015b5461015c5461015d5461015e5461015f546101605461016154610162546101635461016454610165546101665461016754610168546101695461016a5461016b5461016c5461016d5461016e5461016f546101705461017154610172546101735461017454610175546101765461017754610178546101795461017a5461017b5461017c5461017d5461017e5461017f546101805461018154610182546101835461018454610185546101865461018754610188546101895461018a5461018b5461018c5461018d5461018e5461018f546101905461019154610192546101935461019454610195546101965461019754610198546101995461019a5461019b5461019c5461019d5461019e5461019f546101a0546101a1546101a2546101a3546101a4546101a5546101a6546101a7546101a8546101a9546101aa546101ab546101ac546101ad546101ae546101af546101b0546101b1546101b2546101b3546101b4546101b5546101b6546101b7546101b8546101b9546101ba546101bb546101bc546101bd546101be546101bf546101c0546101c1546101c2546101c3546101c4546101c5546101c6546101c7546101c8546101c9546101ca546101cb546101cc546101cd546101ce546101cf546101d0546101d1546101d2546101d3546101d4546101d5546101d6546101d7546101d8546101d9546101da546101db546101dc546101dd546101de546101df546101e0546101e1546101e2546101e3546101e4546101e5546101e6546101e7546101e8546101e9546101ea546101eb546101ec546101ed546101ee546101ef546101f0546101f1546101f2546101f3546101f4546101f5546101f6546101f7546101f8546101f9546101fa546101fb546101fc546101fd546101fe546101ff546102005461020154610202546102035461020454610205546102065461020754610208546102095461020a5461020b5461020c5461020d5461020e5461020f546102105461021154610212546102135461021454610215546102165461021754610218546102195461021a54610221b5461021c5461021d5461021e5461021f546102205461022154610222546102235461022454610225546102265461022754610228546102295461022a5461022b5461022c5461022d5461022e5461022f546102305461023154610232546102335461023454610235546102365461023754610238546102395461023a5461023b5461023c5461023d5461023e5461023f546102405461024154610242546102435461024454610245546102465461024754610248546102495461024a5461024b5461024c5461024d5461024e5461024f546102505461025154610252546102535461025454610255546102565461025754610258546102595461025a5461025b5461025c5461025d5461025e5461025f546102605461026154610262546102635461026454610265546102665461026754610268546102695461026a5461026b5461026c5461026d5461026e5461026f546102705461027154610272546102735461027454610275546102765461027754610278546102795461027a5461027b5461027c5461027d5461027e5461027f546102805461028154610282546102835461028454610285546102865461028754610288546102895461028a5461028b5461028c5461028d5461028e5461028f546102905461029154610292546102935461029454610295546102965461029754610298546102995461029a5461029b5461029c5461029d5461029e5461029f546102a0546102a1546102a2546102a3546102a4546102a5546102a6546102a7546102a8546102a9546102aa546102ab546102ac546102ad546102ae546102af546102b0546102b1546102b2546102b3546102b4546102b5546102b6546102b7546102b8546102b9546102ba546102bb546102bc546102bd546102be546102bf546102c0546102c1546102c2546102c3546102c4546102c5546102c6546102c7546102c8546102c9546102ca546102cb546102cc546102cd546102ce546102cf546102d0546102d1546102d2546102d3546102d4546102d5546102d6546102d7546102d8546102d9546102da546102db546102dc546102dd546102de546102df546102e0546102e1546102e2546102e3546102e4546102e5546102e6546102e7546102e8546102e9546102ea546102eb546102ec546102ed546102ee546102ef546102f0546102f1546102f2546102f3546102f4546102f5546102f6546102f7546102f8546102f9546102fa546102fb546102fc546102fd546102fe546102ff546103005461030154610302546103035461030454610305546103065461030754610308546103095461030a5461030b5461030c5461030d5461030e5461030f546103105461031154610312546103135461031454610315546103165461031754610318546103195461031a5461031b5461031c5461031d5461031e5461031f546103205461032154610322546103235461032454610325546103265461032754610328546103295461032a5461032b5461032c5461032d5461032e5461032f546103305461033154610332546103335461033454610335546103365461033754610338546103395461033a5461033b5461033c5461033d5461033e5461033f546103405461034154610342546103435461034454610345546103465461034754610348546103495461034a5461034b5461034c5461034d5461034e5461034f546103505461035154610352546103535461035454610355546103565461035754610358546103595461035a5461035b5461035c5461035d5461035e5461035f546103605461036154610362546103635461036454610365546103665461036754610368546103695461036a5461036b5461036c5461036d5461036e5461036f546103705461037154610372546103735461037454610375546103765461037754610378546103795461037a5461037b5461037c5461037d5461037e5461037f546103805461038154610382546103835461038454610385546103865461038754610388546103895461038a5461038b5461038c5461038d5461038e5461038f546103905461039154610392546103935461039454610395546103965461039754610398546103995461039a5461039b5461039c5461039d5461039e5461039f546103a0546103a1546103a2546103a3546103a4546103a5546103a6546103a7546103a8546103a9546103aa546103ab546103ac546103ad546103ae546103af546103b0546103b1546103b2546103b3546103b4546103b5546103b6546103b7546103b8546103b9546103ba546103bb546103bc546103bd546103be546103bf546103c0546103c1546103c2546103c3546103c4546103c5546103c6546103c7546103c8546103c9546103ca546103cb546103cc546103cd546103ce546103cf546103d0546103d1546103d2546103d3546103d4546103d5546103d6565b005b60008054906101000a900473ffffffffffffffffffffffffffffffffffffffff1673ffffffffffffffffffffffffffffffffffffffff1663f8a8fd6d826040518263ffffffff1660e01b815260040161028b9190610462565b602060405180830381600087803b1580156102a557600080fd5b505af11580156102b9573d6000803e3d6000fd5b505050506040513d601f19601f820116820180604052508101906102dd91906106a1565b9050919050565b6000819050919050565b6102f7816102e4565b82525050565b600060208201905061031260008301846102ee565b92915050565b600080fd5b600073ffffffffffffffffffffffffffffffffffffffff82169050919050565b60006103488261031d565b9050919050565b6103588161033d565b811461036357600080fd5b50565b6000813590506103758161034f565b92915050565b610384816102e4565b811461038f57600080fd5b50565b6000813590506103a18161037b565b92915050565b600080604083850312156103be576103bd610318565b5b60006103cc85828601610366565b92505060206103dd85828601610392565b9150509250929050565b60008115159050919050565b6103fc816103e7565b82525050565b600060208201905061041760008301846103f3565b92915050565b60006020828403121561043357610432610318565b5b600061044184828501610392565b91505092915050565b610453816102e4565b82525050565b600060208201905061046e600083018461044a565b92915050565b6000819050919050565b600061049961049461048f8461031d565b610474565b61031d565b9050919050565b60006104ab8261047e565b9050919050565b60006104bd826104a0565b9050919050565b6104cd816104b2565b82525050565b600060a0820190506104e860008301886104c4565b6104f5602083018761044a565b610502604083018661044a565b61050f606083018561044a565b61051c608083018461044a565b9695505050505050565b61052f8161033d565b82525050565b600060208201905061054a6000830184610526565b92915050565b600061055b826104a0565b9050919050565b600061056d82610550565b9050919050565b61057d81610562565b82525050565b60006020820190506105986000830184610574565b92915050565b60006105a9826104a0565b9050919050565b6105b98161059e565b82525050565b60006020820190506105d460008301846105b0565b92915050565b60006105e5826104a0565b9050919050565b6105f5816105da565b82525050565b600060208201905061061060008301846105ec565b92915050565b6000610621826104a0565b9050919050565b600061063382610616565b9050919050565b61064381610628565b82525050565b600060208201905061065e600083018461063a565b92915050565b60006020828403121561067a57610679610318565b5b600061068884828501610366565b91505092915050565b6000815190506106a08161037b565b92915050565b6000602082840312156106bc576106bb610318565b5b60006106ca84828501610691565b9150509291505056fea2646970667358221220c8e7b4c6f6b4c6f6b4c6f6b4c6f6b4c6f6b4c6f6b4c6f6b4c6f6b4c6f6b4c6f6b4c6f64736f6c63430008110033"
        
        # Deploy contract if not already deployed
        self.contract_address = os.getenv('CONTRACT_ADDRESS')
        if not self.contract_address:
            self.contract_address = self.deploy_contract()
        else:
            self.contract = self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
    
    def deploy_contract(self):
        """Deploy the contract to blockchain"""
        account = self.w3.eth.accounts[0]
        
        Contract = self.w3.eth.contract(
            abi=self.contract_abi,
            bytecode=self.contract_bytecode
        )
        
        # Build transaction
        transaction = Contract.constructor().buildTransaction({
            'from': account,
            'nonce': self.w3.eth.getTransactionCount(account),
            'gas': 3000000,
            'gasPrice': self.w3.toWei('50', 'gwei')
        })
        
        # Sign and send transaction
        signed_txn = self.w3.eth.account.signTransaction(transaction, 'YOUR_PRIVATE_KEY')
        tx_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        
        # Wait for transaction receipt
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        
        print(f"Contract deployed at: {tx_receipt.contractAddress}")
        return tx_receipt.contractAddress
    
    def generate_product_hash(self, product_data):
        """Generate unique hash for product"""
        data_string = f"{product_data['name']}{product_data['batch_number']}{product_data['manufacturing_date']}"
        return self.w3.keccak(text=data_string).hex()
    
    def register_product(self, product_data, manufacturer_address):
        """Register product on blockchain"""
        product_hash = self.generate_product_hash(product_data)
        
        # Convert to bytes32
        product_hash_bytes = self.w3.toBytes(hexstr=product_hash)
        
        # Get account
        account = self.w3.eth.accounts[0]  # Using first Ganache account for demo
        
        # Create transaction
        transaction = self.contract.functions.registerProduct(
            product_hash_bytes,
            product_data['name'],
            product_data['batch_number']
        ).buildTransaction({
            'from': manufacturer_address or account,
            'nonce': self.w3.eth.getTransactionCount(account),
            'gas': 2000000,
            'gasPrice': self.w3.toWei('50', 'gwei')
        })
        
        # Sign transaction (using first account for demo)
        private_key = '0x' + '1' * 64  # Replace with actual private key from Ganache
        signed_txn = self.w3.eth.account.signTransaction(transaction, private_key)
        
        # Send transaction
        tx_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        
        # Wait for receipt
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        
        return tx_hash.hex(), product_hash, tx_receipt
    
    def transfer_product(self, product_hash, from_address, to_address, transaction_type):
        """Transfer product ownership on blockchain"""
        product_hash_bytes = self.w3.toBytes(hexstr=product_hash)
        
        account = self.w3.eth.accounts[0]
        
        transaction = self.contract.functions.transferProduct(
            product_hash_bytes,
            to_address,
            transaction_type
        ).buildTransaction({
            'from': from_address or account,
            'nonce': self.w3.eth.getTransactionCount(account),
            'gas': 2000000,
            'gasPrice': self.w3.toWei('50', 'gwei')
        })
        
        private_key = '0x' + '1' * 64  # Replace with actual private key
        signed_txn = self.w3.eth.account.signTransaction(transaction, private_key)
        
        tx_hash = self.w3.eth.sendRawTransaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        
        return tx_hash.hex(), tx_receipt
    
    def verify_product(self, product_hash):
        """Verify product on blockchain"""
        try:
            product_hash_bytes = self.w3.toBytes(hexstr=product_hash)
            product_info = self.contract.functions.getProduct(product_hash_bytes).call()
            return {
                'manufacturer': product_info[0],
                'timestamp': product_info[1],
                'exists': product_info[2],
                'productName': product_info[3],
                'batchNumber': product_info[4],
                'blockNumber': product_info[1]  # Using timestamp as block number for demo
            }
        except Exception as e:
            print(f"Verification error: {e}")
            return None
    
    def get_transaction_history(self, product_hash):
        """Get transaction history for a product"""
        # This would require additional contract functions for full implementation
        # For demo, return basic info
        product_info = self.verify_product(product_hash)
        if product_info:
            return [{
                'transactionType': 'Registration',
                'from': '0x0',
                'to': product_info['manufacturer'],
                'timestamp': product_info['timestamp'],
                'blockNumber': product_info['blockNumber']
            }]
        return []
