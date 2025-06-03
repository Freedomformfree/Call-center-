"""
Real SIM800C Hardware Manager
Handles actual physical SIM800C modules with USB sound card integration
"""

import asyncio
import json
import logging
import serial
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import pyaudio
import wave
import threading

logger = logging.getLogger(__name__)

class ModuleStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CALLING = "calling"
    RECEIVING = "receiving"
    ERROR = "error"

@dataclass
class SIM800CModule:
    id: str
    port: str
    baud_rate: int
    gemini_api_key: str
    status: ModuleStatus
    signal_strength: int
    battery_level: int
    network_operator: str
    serial_connection: Optional[serial.Serial] = None
    audio_device_index: Optional[int] = None

class SIM800CManager:
    """Real hardware manager for SIM800C modules"""
    
    def __init__(self):
        self.modules: Dict[str, SIM800CModule] = {}
        self.audio = pyaudio.PyAudio()
        self.active_calls: Dict[str, Dict] = {}
        self.call_recordings: Dict[str, str] = {}
        
    async def initialize_modules(self, config: Dict[str, Any]):
        """Initialize all SIM800C modules from configuration"""
        try:
            for module_id, module_config in config.items():
                await self.add_module(
                    module_id=module_id,
                    port=module_config['port'],
                    baud_rate=module_config.get('baud_rate', 9600),
                    gemini_api_key=module_config['gemini_api_key']
                )
            logger.info(f"Initialized {len(self.modules)} SIM800C modules")
        except Exception as e:
            logger.error(f"Failed to initialize modules: {e}")
            raise
    
    async def add_module(self, module_id: str, port: str, baud_rate: int, gemini_api_key: str):
        """Add and initialize a new SIM800C module"""
        try:
            # Create module instance
            module = SIM800CModule(
                id=module_id,
                port=port,
                baud_rate=baud_rate,
                gemini_api_key=gemini_api_key,
                status=ModuleStatus.DISCONNECTED,
                signal_strength=0,
                battery_level=0,
                network_operator=""
            )
            
            # Attempt serial connection
            try:
                module.serial_connection = serial.Serial(
                    port=port,
                    baudrate=baud_rate,
                    timeout=5,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS
                )
                
                # Test AT command
                if await self._send_at_command(module, "AT"):
                    module.status = ModuleStatus.CONNECTED
                    await self._initialize_module_settings(module)
                    logger.info(f"Module {module_id} connected successfully")
                else:
                    logger.error(f"Module {module_id} AT command failed")
                    
            except serial.SerialException as e:
                logger.error(f"Failed to connect to module {module_id} on {port}: {e}")
                module.status = ModuleStatus.ERROR
            
            # Find audio device
            module.audio_device_index = self._find_audio_device(module_id)
            
            self.modules[module_id] = module
            
        except Exception as e:
            logger.error(f"Failed to add module {module_id}: {e}")
            raise
    
    async def _send_at_command(self, module: SIM800CModule, command: str, timeout: int = 5) -> Optional[str]:
        """Send AT command to SIM800C module"""
        if not module.serial_connection or not module.serial_connection.is_open:
            return None
            
        try:
            # Clear input buffer
            module.serial_connection.reset_input_buffer()
            
            # Send command
            cmd = f"{command}\r\n"
            module.serial_connection.write(cmd.encode())
            
            # Read response
            start_time = time.time()
            response = ""
            
            while time.time() - start_time < timeout:
                if module.serial_connection.in_waiting:
                    data = module.serial_connection.read(module.serial_connection.in_waiting)
                    response += data.decode('utf-8', errors='ignore')
                    
                    if "OK" in response or "ERROR" in response:
                        break
                        
                await asyncio.sleep(0.1)
            
            logger.debug(f"AT Command {command} -> {response.strip()}")
            return response.strip()
            
        except Exception as e:
            logger.error(f"AT command error: {e}")
            return None
    
    async def _initialize_module_settings(self, module: SIM800CModule):
        """Initialize SIM800C module with required settings"""
        try:
            # Set text mode for SMS
            await self._send_at_command(module, "AT+CMGF=1")
            
            # Enable caller ID
            await self._send_at_command(module, "AT+CLIP=1")
            
            # Set audio path
            await self._send_at_command(module, "AT+CHFA=1")
            
            # Get signal strength
            response = await self._send_at_command(module, "AT+CSQ")
            if response and "+CSQ:" in response:
                try:
                    rssi = int(response.split(":")[1].split(",")[0].strip())
                    module.signal_strength = min(100, max(0, (rssi * 100) // 31))
                except:
                    module.signal_strength = 0
            
            # Get network operator
            response = await self._send_at_command(module, "AT+COPS?")
            if response and "+COPS:" in response:
                try:
                    parts = response.split('"')
                    if len(parts) >= 2:
                        module.network_operator = parts[1]
                except:
                    module.network_operator = "Unknown"
            
            # Get battery level (if supported)
            response = await self._send_at_command(module, "AT+CBC")
            if response and "+CBC:" in response:
                try:
                    battery = int(response.split(",")[2])
                    module.battery_level = battery
                except:
                    module.battery_level = 100  # Default if not available
            
        except Exception as e:
            logger.error(f"Failed to initialize module settings: {e}")
    
    def _find_audio_device(self, module_id: str) -> Optional[int]:
        """Find USB sound card device for the module"""
        try:
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if "USB" in device_info['name'] and device_info['maxInputChannels'] > 0:
                    logger.info(f"Found audio device for {module_id}: {device_info['name']}")
                    return i
            return None
        except Exception as e:
            logger.error(f"Failed to find audio device: {e}")
            return None
    
    async def send_sms(self, module_id: str, phone_number: str, message: str) -> Dict[str, Any]:
        """Send SMS using real SIM800C module"""
        module = self.modules.get(module_id)
        if not module or module.status != ModuleStatus.CONNECTED:
            raise Exception(f"Module {module_id} not available")
        
        try:
            # Set SMS text mode
            await self._send_at_command(module, "AT+CMGF=1")
            
            # Set phone number
            response = await self._send_at_command(module, f'AT+CMGS="{phone_number}"')
            if not response or ">" not in response:
                raise Exception("Failed to set SMS recipient")
            
            # Send message (Ctrl+Z = ASCII 26)
            message_cmd = f"{message}\x1A"
            module.serial_connection.write(message_cmd.encode())
            
            # Wait for response
            response = ""
            start_time = time.time()
            while time.time() - start_time < 30:  # 30 second timeout
                if module.serial_connection.in_waiting:
                    data = module.serial_connection.read(module.serial_connection.in_waiting)
                    response += data.decode('utf-8', errors='ignore')
                    
                    if "+CMGS:" in response:
                        # SMS sent successfully
                        message_id = response.split(":")[1].strip()
                        logger.info(f"SMS sent successfully: {message_id}")
                        return {
                            "success": True,
                            "message_id": message_id,
                            "module_id": module_id,
                            "timestamp": time.time()
                        }
                    elif "ERROR" in response:
                        raise Exception(f"SMS send error: {response}")
                
                await asyncio.sleep(0.5)
            
            raise Exception("SMS send timeout")
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
            raise
    
    async def make_call(self, module_id: str, phone_number: str) -> Dict[str, Any]:
        """Make voice call using real SIM800C module"""
        module = self.modules.get(module_id)
        if not module or module.status != ModuleStatus.CONNECTED:
            raise Exception(f"Module {module_id} not available")
        
        try:
            # Initiate call
            response = await self._send_at_command(module, f"ATD{phone_number};", timeout=30)
            
            if response and ("OK" in response or "CONNECT" in response):
                call_id = f"call_{int(time.time())}"
                module.status = ModuleStatus.CALLING
                
                self.active_calls[call_id] = {
                    "module_id": module_id,
                    "phone_number": phone_number,
                    "start_time": time.time(),
                    "status": "connecting"
                }
                
                # Start call monitoring
                asyncio.create_task(self._monitor_call(module, call_id))
                
                logger.info(f"Call initiated: {call_id}")
                return {
                    "success": True,
                    "call_id": call_id,
                    "module_id": module_id,
                    "status": "connecting"
                }
            else:
                raise Exception(f"Call initiation failed: {response}")
                
        except Exception as e:
            logger.error(f"Failed to make call: {e}")
            raise
    
    async def _monitor_call(self, module: SIM800CModule, call_id: str):
        """Monitor call status and handle audio"""
        try:
            call_info = self.active_calls[call_id]
            
            # Wait for call connection
            connected = False
            start_time = time.time()
            
            while time.time() - start_time < 30:  # 30 second timeout
                if module.serial_connection.in_waiting:
                    response = module.serial_connection.read(module.serial_connection.in_waiting)
                    response_str = response.decode('utf-8', errors='ignore')
                    
                    if "CONNECT" in response_str:
                        connected = True
                        call_info["status"] = "connected"
                        module.status = ModuleStatus.CALLING
                        break
                    elif "NO CARRIER" in response_str or "BUSY" in response_str:
                        call_info["status"] = "failed"
                        break
                
                await asyncio.sleep(0.5)
            
            if connected:
                # Start audio recording if device available
                if module.audio_device_index is not None:
                    await self._start_call_recording(module, call_id)
                
                # Monitor for call end
                while call_id in self.active_calls:
                    if module.serial_connection.in_waiting:
                        response = module.serial_connection.read(module.serial_connection.in_waiting)
                        response_str = response.decode('utf-8', errors='ignore')
                        
                        if "NO CARRIER" in response_str:
                            call_info["status"] = "ended"
                            call_info["end_time"] = time.time()
                            break
                    
                    await asyncio.sleep(1)
            
            # Cleanup
            if call_id in self.active_calls:
                del self.active_calls[call_id]
            module.status = ModuleStatus.CONNECTED
            
        except Exception as e:
            logger.error(f"Call monitoring error: {e}")
    
    async def _start_call_recording(self, module: SIM800CModule, call_id: str):
        """Start recording call audio"""
        try:
            if module.audio_device_index is None:
                return
            
            # Audio recording parameters
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            # Start recording in separate thread
            def record_audio():
                try:
                    stream = self.audio.open(
                        format=format,
                        channels=channels,
                        rate=rate,
                        input=True,
                        input_device_index=module.audio_device_index,
                        frames_per_buffer=chunk
                    )
                    
                    frames = []
                    recording = True
                    
                    while recording and call_id in self.active_calls:
                        try:
                            data = stream.read(chunk, exception_on_overflow=False)
                            frames.append(data)
                        except:
                            break
                    
                    stream.stop_stream()
                    stream.close()
                    
                    # Save recording
                    if frames:
                        filename = f"/tmp/call_{call_id}.wav"
                        wf = wave.open(filename, 'wb')
                        wf.setnchannels(channels)
                        wf.setsampwidth(self.audio.get_sample_size(format))
                        wf.setframerate(rate)
                        wf.writeframes(b''.join(frames))
                        wf.close()
                        
                        self.call_recordings[call_id] = filename
                        logger.info(f"Call recording saved: {filename}")
                
                except Exception as e:
                    logger.error(f"Recording error: {e}")
            
            # Start recording thread
            recording_thread = threading.Thread(target=record_audio)
            recording_thread.daemon = True
            recording_thread.start()
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
    
    async def hang_up_call(self, call_id: str) -> bool:
        """Hang up active call"""
        if call_id not in self.active_calls:
            return False
        
        try:
            call_info = self.active_calls[call_id]
            module = self.modules.get(call_info["module_id"])
            
            if module and module.serial_connection:
                await self._send_at_command(module, "ATH")
                
            call_info["status"] = "ended"
            call_info["end_time"] = time.time()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to hang up call: {e}")
            return False
    
    async def get_module_status(self, module_id: str) -> Dict[str, Any]:
        """Get real-time status of SIM800C module"""
        module = self.modules.get(module_id)
        if not module:
            raise Exception(f"Module {module_id} not found")
        
        # Update signal strength
        if module.status == ModuleStatus.CONNECTED:
            response = await self._send_at_command(module, "AT+CSQ")
            if response and "+CSQ:" in response:
                try:
                    rssi = int(response.split(":")[1].split(",")[0].strip())
                    module.signal_strength = min(100, max(0, (rssi * 100) // 31))
                except:
                    pass
        
        return {
            "id": module.id,
            "status": module.status.value,
            "signal_strength": module.signal_strength,
            "battery_level": module.battery_level,
            "network_operator": module.network_operator,
            "port": module.port,
            "audio_device": module.audio_device_index is not None
        }
    
    async def list_modules(self) -> List[Dict[str, Any]]:
        """List all SIM800C modules with current status"""
        modules_status = []
        for module_id in self.modules:
            try:
                status = await self.get_module_status(module_id)
                modules_status.append(status)
            except Exception as e:
                logger.error(f"Failed to get status for module {module_id}: {e}")
                modules_status.append({
                    "id": module_id,
                    "status": "error",
                    "error": str(e)
                })
        
        return modules_status
    
    async def get_active_calls(self) -> List[Dict[str, Any]]:
        """Get list of active calls"""
        return list(self.active_calls.values())
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            # Close all serial connections
            for module in self.modules.values():
                if module.serial_connection and module.serial_connection.is_open:
                    module.serial_connection.close()
            
            # Close audio
            self.audio.terminate()
            
            logger.info("SIM800C manager cleanup completed")
            
        except Exception as e:
            logger.error(f"Cleanup error: {e}")