from fastapi import APIRouter, Depends, status, Response, HTTPException, Body, Header
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from typing import List, Optional, Dict, Any
from ..database import get_db
from .. import jwt_handler, models, schemas
from pydantic import BaseModel
import logging
from datetime import date, datetime

