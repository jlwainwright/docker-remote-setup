import requests
import json 
import hashlib
import logging
import time 

class aquatempConnect():
    _cloudURL = "https://cloud.linked-go.com:449/crmservice/api"        #requires TLSv1.1
    _token = ""
    _tokenTimestamp = 0
    _header = {
        "Content-Type": "application/json",
        "charset": "utf-8",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15",
        "Accept": "application/json",
        "Connection": "keep-alive"
    }

    def __init__(self, username, password):
        # Setup logging
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        self._username = username
        self._password = str(hashlib.md5(password.encode()).hexdigest())
        self.devices = []
        self.checkToken()               #Initial login       
        self.get_devices()

    def get_devices(self):
        """Get the list of available devices"""
        try:
            # Add timestamp to prevent caching
            params = {
                "timestamp": int(time.time() * 1000),
                "lang": "en_US",
                "type": "1",  # Try different type parameter
                "token": self._token  # Include token in params
            }
            
            r = requests.post(
                self._cloudURL+"/app/device/deviceList", 
                headers=self._header,
                params=params,
                verify=False  # Try without SSL verification
            )
            
            self.logger.debug("=== Device List Request ===")
            self.logger.debug(f"URL: {r.url}")
            self.logger.debug(f"Headers: {self._header}")
            self.logger.debug(f"Params: {params}")
            self.logger.debug(f"Status Code: {r.status_code}")
            self.logger.debug(f"Response Headers: {dict(r.headers)}")
            self.logger.debug(f"Raw Response: {r.text}")
            
            response_json = r.json()
            self.logger.debug(f"Parsed Response: {json.dumps(response_json, indent=2)}")
            
            if response_json["error_code"] != "0":
                raise Exception(f"Failed to get device list: {response_json['error_msg']}")
            
            if "objectResult" not in response_json:
                self.logger.error(f"Invalid API response structure: {response_json}")
                raise Exception("Invalid API response: missing device list")
                
            self.devices = response_json.get("objectResult", [])
            self.logger.info(f"Device list response: {self.devices}")
            
            if not self.devices:
                self.logger.warning("No devices found in the API response")
                raise Exception("No devices found in your account. Please ensure your device is properly registered.")
            
            self.logger.info(f"Found {len(self.devices)} device(s)")
            for device in self.devices:
                self.logger.info(f"Device: {device.get('device_name', 'Unknown')} (ID: {device.get('device_code', 'Unknown')})")
            return self.devices
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error getting devices: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Invalid JSON response: {str(e)}")
            raise Exception(f"Invalid API response format: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error getting devices: {str(e)}")
            raise

    def checkToken(self):
        if self._token == "" or (time.time()-self._tokenTimestamp>3600):
            self.logger.info("Getting a new token")
            try:
                # Add additional parameters that might be required
                payload = {
                    "userName": self._username,
                    "password": self._password,
                    "type": "2",
                    "lang": "en_US",
                    "timestamp": int(time.time() * 1000),
                    "appid": "AQUATEMP_APP",  # Try adding app identifier
                    "platform": "ios"  # Specify platform
                }
                
                r = requests.post(
                    self._cloudURL+"/app/user/login",
                    headers=self._header,
                    json=payload,
                    verify=False  # Try without SSL verification
                )
                
                self.logger.debug("=== Login Request ===")
                self.logger.debug(f"URL: {r.url}")
                self.logger.debug(f"Headers: {self._header}")
                self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
                self.logger.debug(f"Status Code: {r.status_code}")
                self.logger.debug(f"Response Headers: {dict(r.headers)}")
                self.logger.debug(f"Raw Response: {r.text}")
                
                response_json = r.json()
                self.logger.debug(f"Parsed Response: {json.dumps(response_json, indent=2)}")
                
                if response_json["error_code"] != "0":
                    error_msg = response_json["error_msg"]
                    if "用户不存在" in error_msg:
                        raise Exception("Invalid username or password")
                    elif "密码错误" in error_msg:
                        raise Exception("Incorrect password")
                    else:
                        raise Exception(f"Connection Error: {error_msg}")
                
                if "objectResult" not in response_json or "x-token" not in response_json["objectResult"]:
                    self.logger.error(f"Invalid login response structure: {response_json}")
                    raise Exception("Invalid login response: missing token")
                
                self._token = response_json["objectResult"]["x-token"]
                self._header["x-token"] = self._token
                self._tokenTimestamp = time.time()
                self.logger.debug("Token updated successfully")
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Network error during login: {str(e)}")
                raise Exception(f"Network error: {str(e)}")
            except ValueError as e:
                self.logger.error(f"Invalid JSON in login response: {str(e)}")
                raise Exception(f"Invalid API response format: {str(e)}")
            except Exception as e:
                self.logger.error(f"Login error: {str(e)}")
                raise
        return(self._token)

    def setPower(self, state, dev=0):
        payload = {"param":[{"deviceCode": self.devices[dev]["device_code"], "protocolCode": "Power","value": str(state)}]}
        r = requests.post(self._cloudURL+"/app/device/control", headers=self._header, json=payload)
        response_json = r.json()
        self.logger.debug(f"Set power response: {response_json}")
        if response_json["error_code"] != "0": self.logger.debug(f"Set power not successful. Error message {response_json['error_msg']}")
        
    def setTemperature(self, temp, mode=None, dev=0):
        # set temperature for the current mode if not specified. R01: cooling, R02: heating, R03: auto
        if mode is None: mode = self.getStatus()["Mode"]
        payload = {"param":[{"deviceCode": self.devices[dev]["device_code"], "protocolCode": "R0"+str(mode),"value": str(temp)}]}
        r = requests.post(self._cloudURL+"/app/device/control", headers=self._header, json=payload)
        response_json = r.json()
        self.logger.debug(f"Set temperature response: {response_json}")
        if response_json["error_code"] != "0": self.logger.debug(f"Set temperature not successful. Error message {response_json['error_msg']}")

    def setSilent(self, state="1", dev=0):
        #set silent mode. Default is to set to silent
        payload = {"param":[{"deviceCode": self.devices[dev]["device_code"], "protocolCode": "Manual-mute","value": str(state)}]}
        r = requests.post(self._cloudURL+"/app/device/control", headers=self._header, json=payload)
        response_json = r.json()
        self.logger.debug(f"Set silent response: {response_json}")
        if response_json["error_code"] != "0": self.logger.debug(f"Set silent not successful. Error message {response_json['error_msg']}") 
         
    def getStatus(self, dev=0):
        try:
            self.checkToken()  # Ensure token is valid before getting status
            
            codes = {
                    "T01":"Suction Temp",
                    "T02":"Inlet Water Temp",
                    "T03":"Outlet Water Temp",
                    "T04":"Coil 1 Temp",
                    "T05":"Ambient Temp",
                    "T07":"Compressor Current",
                    "T09":"Flow Rate Input"
            }
                    
            payload = {"deviceCode": self.devices[dev]["device_code"], 
                      "protocalCodes":["Power","Mode","Manual-mute","T01","T02","2074","2075","2076","2077",
                                     "H03","Set_Temp","R08","R09","R10","R11","R01","R02","R03","T03","1158",
                                     "1159","F17","H02","T04","T05","T07","T14","T17"]}
            r = requests.post(self._cloudURL+"/app/device/getDataByCode", headers=self._header, json=payload)
            response_json = r.json()
            self.logger.debug(f"Get status response: {response_json}")
            
            if response_json["error_code"] == "0":
                statusMap = {}
                for d in response_json["objectResult"]:
                    statusMap[d["code"]] = d["value"]
                return statusMap
            else:
                error_msg = response_json["error_msg"]
                self.logger.error(f"Get status failed: {error_msg}")
                raise Exception(f"Failed to get status: {error_msg}")
        except Exception as e:
            self.logger.error(f"Error in getStatus: {str(e)}")
            raise
