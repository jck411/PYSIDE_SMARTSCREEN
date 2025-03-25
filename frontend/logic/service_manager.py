#!/usr/bin/env python3
import asyncio
import aiohttp
import logging

from frontend.config import HTTP_BASE_URL, logger

class ServiceManager:
    """
    Manages service-level operations like stopping message generation
    and handling other API endpoints.
    """
    def __init__(self):
        self._loop = asyncio.get_event_loop()
        logger.info("[ServiceManager] Initialized")
        
    async def stop_generation(self):
        """Stop ongoing message generation on the server"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{HTTP_BASE_URL}/api/stop-generation") as resp:
                    resp_data = await resp.json()
                    logger.info(f"[ServiceManager] Stop generation response: {resp_data}")
            return True
        except Exception as e:
            logger.error(f"[ServiceManager] Error stopping generation: {e}")
            return False
            
    async def stop_all_services(self):
        """Stop all ongoing services on the server side"""
        results = {
            "generation_stopped": False,
            "audio_stopped": False
        }
        
        try:
            # Create a client session for both requests
            async with aiohttp.ClientSession() as session:
                # Stop audio first
                async with session.post(f"{HTTP_BASE_URL}/api/stop-audio") as resp1:
                    resp1_data = await resp1.json()
                    results["audio_stopped"] = resp1_data.get("success", False)
                    logger.info(f"[ServiceManager] Stop audio response: {resp1_data}")

                # Then stop generation
                async with session.post(f"{HTTP_BASE_URL}/api/stop-generation") as resp2:
                    resp2_data = await resp2.json()
                    results["generation_stopped"] = resp2_data.get("success", False)
                    logger.info(f"[ServiceManager] Stop generation response: {resp2_data}")
                    
            return results
        except Exception as e:
            logger.error(f"[ServiceManager] Error stopping services: {e}")
            return results
