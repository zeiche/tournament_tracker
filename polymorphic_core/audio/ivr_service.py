#!/usr/bin/env python3
"""
Polymorphic IVR Service - Platform-agnostic Interactive Voice Response
Handles call flow logic independent of telephony platform (Twilio, etc.)
"""

from typing import Dict, Any, Callable, Optional
from polymorphic_core import register_capability
from polymorphic_core.local_bonjour import local_announcer
import asyncio
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class IVRResponse:
    """Response from IVR processing"""
    action: str  # 'speak', 'hangup', 'transfer', 'collect'
    content: str = ""
    next_state: Optional[str] = None
    metadata: Dict[str, Any] = None

class IVRScriptHandler(ABC):
    """Abstract interface for any type of IVR script handler"""
    
    @abstractmethod
    async def start_call(self, call_id: str, context: Dict[str, Any]) -> IVRResponse:
        """Start a call with this script"""
        pass
    
    @abstractmethod  
    async def process_signal(self, call_id: str, signal_type: str, signal_data: str) -> IVRResponse:
        """Process incoming signal (DTMF, Speech, etc.)"""
        pass
    
    @abstractmethod
    async def end_call(self, call_id: str):
        """End call and cleanup"""
        pass

class ClassBasedScriptHandler(IVRScriptHandler):
    """Handler for Python class-based scripts"""
    
    def __init__(self, script_instance):
        self.script = script_instance
    
    async def start_call(self, call_id: str, context: Dict[str, Any]) -> IVRResponse:
        return await self.script.on_call_start(call_id, None, None, context)
    
    async def process_signal(self, call_id: str, signal_type: str, signal_data: str) -> IVRResponse:
        if signal_type.lower() == 'dtmf':
            return await self.script.on_dtmf_input(call_id, signal_data, None, None)
        elif signal_type.lower() == 'speech':
            return await self.script.on_speech_input(call_id, signal_data, None, None)
        else:
            return IVRResponse("continue", f"Unknown signal type: {signal_type}")
    
    async def end_call(self, call_id: str):
        await self.script.on_call_end(call_id, None, None)

class ProcessBasedScriptHandler(IVRScriptHandler):
    """Handler for external process-based scripts"""
    
    def __init__(self, process_command: str, process_args: list = None):
        self.command = process_command
        self.args = process_args or []
        self.processes = {}  # call_id -> subprocess
    
    async def start_call(self, call_id: str, context: Dict[str, Any]) -> IVRResponse:
        import asyncio
        import json
        
        # Start the script process for this call
        cmd = [self.command] + self.args + [f"--call-id={call_id}", "--action=start"]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            self.processes[call_id] = process
            
            # Send context data
            context_json = json.dumps(context)
            process.stdin.write(context_json.encode() + b'\n')
            await process.stdin.drain()
            
            # Read response
            response_line = await process.stdout.readline()
            response_data = json.loads(response_line.decode().strip())
            
            return IVRResponse(
                response_data.get('action', 'continue'),
                response_data.get('content', ''),
                response_data.get('next_state'),
                response_data.get('metadata', {})
            )
            
        except Exception as e:
            print(f"❌ Error starting process script: {e}")
            return IVRResponse("speak", "Script error occurred", "error")
    
    async def process_signal(self, call_id: str, signal_type: str, signal_data: str) -> IVRResponse:
        import json
        
        process = self.processes.get(call_id)
        if not process:
            return IVRResponse("speak", "No active script process", "error")
        
        try:
            # Send signal to process
            signal_msg = {
                'type': signal_type,
                'data': signal_data,
                'call_id': call_id
            }
            process.stdin.write(json.dumps(signal_msg).encode() + b'\n')
            await process.stdin.drain()
            
            # Read response
            response_line = await process.stdout.readline()
            response_data = json.loads(response_line.decode().strip())
            
            return IVRResponse(
                response_data.get('action', 'continue'),
                response_data.get('content', ''),
                response_data.get('next_state'),
                response_data.get('metadata', {})
            )
            
        except Exception as e:
            print(f"❌ Error communicating with process script: {e}")
            return IVRResponse("speak", "Script communication error", "error")
    
    async def end_call(self, call_id: str):
        process = self.processes.get(call_id)
        if process:
            try:
                # Send end signal
                import json
                end_msg = {'type': 'end_call', 'call_id': call_id}
                process.stdin.write(json.dumps(end_msg).encode() + b'\n')
                await process.stdin.drain()
                
                # Give process time to cleanup
                await asyncio.sleep(0.1)
                
                # Terminate if still running
                if process.returncode is None:
                    process.terminate()
                    await process.wait()
                    
            except Exception as e:
                print(f"❌ Error ending process script: {e}")
            finally:
                if call_id in self.processes:
                    del self.processes[call_id]

class HTTPScriptHandler(IVRScriptHandler):
    """Handler for HTTP-based script services"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
    
    async def start_call(self, call_id: str, context: Dict[str, Any]) -> IVRResponse:
        import aiohttp
        import json
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/start_call",
                    json={'call_id': call_id, 'context': context}
                ) as response:
                    data = await response.json()
                    return IVRResponse(
                        data.get('action', 'continue'),
                        data.get('content', ''),
                        data.get('next_state'),
                        data.get('metadata', {})
                    )
        except Exception as e:
            print(f"❌ Error calling HTTP script: {e}")
            return IVRResponse("speak", "Remote script error", "error")
    
    async def process_signal(self, call_id: str, signal_type: str, signal_data: str) -> IVRResponse:
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/process_signal",
                    json={
                        'call_id': call_id,
                        'signal_type': signal_type, 
                        'signal_data': signal_data
                    }
                ) as response:
                    data = await response.json()
                    return IVRResponse(
                        data.get('action', 'continue'),
                        data.get('content', ''),
                        data.get('next_state'),
                        data.get('metadata', {})
                    )
        except Exception as e:
            print(f"❌ Error calling HTTP script: {e}")
            return IVRResponse("speak", "Remote script error", "error")
    
    async def end_call(self, call_id: str):
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/end_call",
                    json={'call_id': call_id}
                ):
                    pass
        except Exception as e:
            print(f"❌ Error ending HTTP script: {e}")

class PolymorphicIVR:
    """Truly polymorphic IVR service - scripts can be classes, processes, or services"""
    
    def __init__(self):
        self.script_handlers = {}  # script_name -> IVRScriptHandler 
        self.active_calls = {}  # call_id -> call_state
        
        # Register as IVR service
        register_capability('ivr_service', self)
        
        # Announce our service locally
        local_announcer.announce(
            "Polymorphic IVR Service",
            [
                "I handle Interactive Voice Response logic for any platform",
                "I process DTMF and Speech signals to drive call flows",
                "I execute IVR scripts independent of telephony platform",
                "I provide response handlers for different menu options",
                "I maintain call state and context across interactions",
                "I support dynamic script loading and custom handlers"
            ]
        )
    
    def register_script_handler(self, script_name: str, handler: IVRScriptHandler):
        """Register a polymorphic script handler (class, process, HTTP service, etc.)"""
        self.script_handlers[script_name] = handler
        
        handler_type = type(handler).__name__
        local_announcer.announce(
            f"IVR_SCRIPT_REGISTERED",
            [
                f"SCRIPT: {script_name}",
                f"TYPE: {handler_type}",
                f"HANDLER: {handler.__class__.__module__}.{handler.__class__.__name__}"
            ]
        )
        print(f"📋 IVR Script registered: {script_name} ({handler_type})")
    
    def register_class_script(self, script_name: str, script_instance):
        """Convenience method to register a Python class script"""
        handler = ClassBasedScriptHandler(script_instance)
        self.register_script_handler(script_name, handler)
    
    def register_process_script(self, script_name: str, command: str, args: list = None):
        """Convenience method to register a process-based script"""
        handler = ProcessBasedScriptHandler(command, args)
        self.register_script_handler(script_name, handler)
    
    def register_http_script(self, script_name: str, base_url: str):
        """Convenience method to register an HTTP-based script"""
        handler = HTTPScriptHandler(base_url)
        self.register_script_handler(script_name, handler)
    
    async def start_call(self, call_id: str, script_name: str, initial_context: Dict[str, Any] = None) -> IVRResponse:
        """Start a new call with specified script handler"""
        if script_name not in self.script_handlers:
            return IVRResponse("speak", f"Script {script_name} not found", "error")
        
        handler = self.script_handlers[script_name]
        context = initial_context or {}
        
        # Initialize call state
        self.active_calls[call_id] = {
            'script_name': script_name,
            'context': context,
            'input_history': []
        }
        
        # Start call with script handler
        try:
            response = await handler.start_call(call_id, context)
            
            local_announcer.announce(
                "IVR_CALL_STARTED",
                [
                    f"CALL_ID: {call_id}",
                    f"SCRIPT: {script_name}",
                    f"HANDLER: {type(handler).__name__}"
                ]
            )
            
            return response
            
        except Exception as e:
            print(f"❌ Error starting call with script {script_name}: {e}")
            return IVRResponse("speak", "Script startup error", "error")
    
    async def process_input(self, call_id: str, input_type: str, input_value: str) -> IVRResponse:
        """Process DTMF or Speech input through polymorphic script handler"""
        if call_id not in self.active_calls:
            return IVRResponse("speak", "Call not found", "error")
        
        call_state = self.active_calls[call_id]
        script_name = call_state['script_name']
        handler = self.script_handlers.get(script_name)
        
        if not handler:
            return IVRResponse("speak", "Script handler not found", "error")
        
        # Log input
        call_state['input_history'].append({
            'type': input_type,
            'value': input_value,
            'timestamp': asyncio.get_event_loop().time()
        })
        
        print(f"🎛️ IVR processing: {input_type}='{input_value}' for call {call_id} via {type(handler).__name__}")
        
        # Process input through polymorphic handler
        try:
            response = await handler.process_signal(call_id, input_type, input_value)
            return response
            
        except Exception as e:
            print(f"❌ Error processing input with script {script_name}: {e}")
            return IVRResponse("speak", "Script processing error", "error")
    
    async def _process_state(self, call_id: str, state_name: str) -> IVRResponse:
        """Process current state and generate response"""
        call_state = self.active_calls[call_id]
        script = self.scripts[call_state['script_name']]
        
        state_config = script.get_state_config(state_name)
        if not state_config:
            return IVRResponse("speak", "System error", "error")
        
        # Check if we have a custom handler for this state
        handlers = self.response_handlers.get(call_state['script_name'], {})
        if state_name in handlers:
            # Use custom handler
            handler_response = await handlers[state_name](call_id, call_state['context'])
            if handler_response:
                return handler_response
        
        # Use default state processing
        response_text = state_config.get('prompt', 'Please make a selection')
        action = state_config.get('action', 'speak')
        
        return IVRResponse(action, response_text, state_name)
    
    async def _handle_invalid_input(self, call_id: str, state_name: str, input_type: str, input_value: str) -> IVRResponse:
        """Handle invalid input"""
        call_state = self.active_calls[call_id]
        script = self.scripts[call_state['script_name']]
        
        state_config = script.get_state_config(state_name)
        invalid_prompt = state_config.get('invalid_prompt', f"Invalid selection '{input_value}'. Please try again.")
        
        return IVRResponse("speak", invalid_prompt, state_name)
    
    def end_call(self, call_id: str):
        """End call and cleanup state"""
        if call_id in self.active_calls:
            call_info = self.active_calls[call_id]
            del self.active_calls[call_id]
            
            local_announcer.announce(
                "IVR_CALL_ENDED",
                [
                    f"CALL_ID: {call_id}",
                    f"SCRIPT: {call_info['script_name']}",
                    f"FINAL_STATE: {call_info.get('current_state', 'unknown')}",
                    f"INPUTS: {len(call_info['input_history'])}"
                ]
            )
            print(f"📞 IVR call ended: {call_id}")
    
    def get_call_status(self, call_id: str) -> Dict[str, Any]:
        """Get status of active call"""
        if call_id in self.active_calls:
            return self.active_calls[call_id].copy()
        return {"status": "not_found"}

class IVRScript:
    """IVR Script definition"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.states = config.get('states', {})
        self.initial_state = config.get('initial_state', 'main_menu')
    
    async def process_input(self, current_state: str, input_type: str, input_value: str, context: Dict[str, Any]) -> Optional[str]:
        """Process input and return next state"""
        state_config = self.states.get(current_state, {})
        transitions = state_config.get('transitions', {})
        
        # Check for direct input mapping
        if input_value in transitions:
            return transitions[input_value]
        
        # Check for input type mapping
        type_transitions = transitions.get(input_type.lower(), {})
        if input_value in type_transitions:
            return type_transitions[input_value]
        
        return None
    
    def get_state_config(self, state_name: str) -> Dict[str, Any]:
        """Get configuration for a state"""
        return self.states.get(state_name, {})

# Global IVR instance
_ivr_service = None

def get_ivr_service():
    """Get the global IVR service instance"""
    global _ivr_service
    if _ivr_service is None:
        _ivr_service = PolymorphicIVR()
    return _ivr_service

if __name__ == "__main__":
    # Test the IVR service
    ivr = get_ivr_service()
    print("🎛️ Polymorphic IVR Service running...")
    print("📋 Ready to process call scripts and handle interactions")