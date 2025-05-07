import logging
from typing import Dict, List, Any
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

logger = logging.getLogger(__name__)


class ProductDatabase:
    
    def __init__(self, config=None):
        self.config = config or DB_CONFIG["mysql"]
        self.connection = None
        self.connect()
    
    def connect(self):
        try:
            self.connection = mysql.connector.connect(
                host=self.config["host"],
                port=self.config["port"],
                user=self.config["user"],
                password=self.config["password"],
                database=self.config["database"],
                charset=self.config["charset"]
            )
            logger.info("数据库连接成功")
        except Error as e:
            logger.error(f"数据库连接失败: {e}")
            self.connection = None
    
    def reconnect_if_needed(self):
        try:
            if self.connection is None or not self.connection.is_connected():
                logger.info("重新连接数据库")
                self.connect()
        except Exception as e:
            logger.error(f"重新连接数据库失败: {e}")
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def get_product_data(self, product_number: str, attributes: List[str]) -> Dict[str, Any]:
        """
        获取产品特定属性的数据
        
        Args:
            product_number: 产品货号
            attributes: 需要获取的属性列表
            
        Returns:
            Dict[str, Any]: 属性名称和值的字典
        """
        self.reconnect_if_needed()
        result = {}
        
        if not self.connection:
            logger.warning("数据库未连接，无法获取产品数据")
            return result
        
        try:
            # 首先，根据product_number从productbaseinfo表中查询产品ID和original_product_number
            base_query = """
            SELECT id, original_product_number
            FROM intrinsic_attributes_productbaseinfo
            WHERE product_number = %s
            LIMIT 1
            """
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(base_query, (product_number,))
            
            product_row = cursor.fetchone()
            
            if not product_row:
                logger.warning(f"找不到产品: {product_number}")
                cursor.close()
                return result
                
            product_id = product_row['id']
            original_product_number = product_row.get('original_product_number', product_number)
            logger.info(f"找到产品ID: {product_id}, 原始产品编号: {original_product_number}")
            
            # 查询材质信息和尺寸信息
            self.query_material_data(product_id, attributes, result)
            self.query_size_data(original_product_number, attributes, result)
            
            cursor.close()
        
        except Exception as e:
            logger.error(f"查询产品数据失败: {e}")
        
        return result
    
    def query_material_data(self, product_id: int, attributes: List[str], result: Dict[str, Any]) -> None:
        """
        查询产品材质数据
        
        Args:
            product_id: 产品ID
            attributes: 要查询的属性列表
            result: 结果字典，将直接修改此字典
        """
        try:
            # 查询材质数据
            material_query = """
            SELECT *
            FROM intrinsic_attributes_productmaterial
            WHERE product_id = %s
            LIMIT 1
            """
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(material_query, (product_id,))
            material_row = cursor.fetchone()
            cursor.close()
            
            if material_row:
                logger.info(f"找到产品材质数据")
                
                # 处理材质属性
                self.process_attributes(attributes, material_row, result, {
                    "鞋面材质": "upper",
                    "内里材质": "lining",
                    "鞋底材质": "outsole",
                    "鞋垫材质": "insole"
                })
            else:
                logger.warning(f"找不到产品材质数据: product_id={product_id}")
                
        except Exception as e:
            logger.error(f"查询材质数据失败: {e}")
    
    def query_size_data(self, original_product_number: str, attributes: List[str], result: Dict[str, Any]) -> None:
        """
        查询产品尺寸数据
        
        Args:
            original_product_number: 原始产品编号
            attributes: 要查询的属性列表
            result: 结果字典，将直接修改此字典
        """
        try:
            # 查询尺寸数据
            size_query = """
            SELECT *
            FROM intrinsic_attributes_productsize
            WHERE original_product_number = %s
            LIMIT 1
            """
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(size_query, (original_product_number,))
            size_row = cursor.fetchone()
            cursor.close()
            
            if size_row:
                logger.info(f"找到产品尺寸数据")
                
                # 处理尺寸属性
                self.process_attributes(attributes, size_row, result, {
                    "后跟高": "heel_height",
                    "靴筒高度": "boot_shaft_height",
                    "鞋跟高度": "heel_height",
                    "鞋底厚度": "platform_height"
                })
            else:
                logger.warning(f"找不到产品尺寸数据: original_product_number={original_product_number}")
                
        except Exception as e:
            logger.error(f"查询尺寸数据失败: {e}")
    
    def process_attributes(self, attributes: List[str], row_data: Dict[str, Any], 
                           result: Dict[str, Any], field_mapping: Dict[str, str]) -> None:
        """
        处理属性数据，从数据行中提取属性值到结果字典
        
        Args:
            attributes: 要查询的属性列表
            row_data: 数据行
            result: 结果字典，将直接修改此字典
            field_mapping: 属性名到字段名的映射
        """
        for attr in attributes:
            if attr in row_data:
                result[attr] = row_data[attr]
            
            mapped_field = field_mapping.get(attr)
            if mapped_field and mapped_field in row_data:
                result[attr] = row_data[mapped_field]
            
            # 尝试通过别名匹配（数据库字段可能与请求属性名不完全一致）
            if attr not in result:
                for field, value in row_data.items():
                    # 简单的匹配逻辑：检查属性名是否是字段的一部分，或字段是否是属性名的一部分
                    if (attr.lower() in field.lower() or field.lower() in attr.lower()) and attr not in result:
                        result[attr] = value
                        break
    
    def get_attribute_values(self, attribute_name: str) -> List[str]:
        """
        获取某个属性的所有可能值
        
        Args:
            attribute_name: 属性名称
            
        Returns:
            List[str]: 该属性的所有已知值
        """
        self.reconnect_if_needed()
        results = []
        
        if not self.connection:
            logger.warning("数据库未连接，无法获取属性值")
            return results
        
        try:
            # 映射常见的属性名对应的字段名
            field_mapping = {
                "鞋面材质": "upper",
                "内里材质": "lining",
                "鞋底材质": "outsole",
                "鞋垫材质": "insole",
                "闭合方式": "closure_type",
                "鞋头款式": "toe_shape",
                "后跟高": "heel_height",
                "靴筒高度": "tube_height",
                "鞋跟高度": "heel_height",
                "鞋跟款式": "heel_shape",
            }
            
            # 尝试找到对应的字段名
            field_name = field_mapping.get(attribute_name, attribute_name)
            
            # 构建查询SQL（简单防止SQL注入）
            safe_field_name = field_name.replace("'", "''")
            
            # 检查各个表中是否存在该字段并获取值
            tables_to_check = [
                "intrinsic_attributes_productmaterial",  # 材质表
                "intrinsic_attributes_productsize",      # 尺寸表
                "intrinsic_attributes_productbaseinfo"   # 基本信息表
            ]
            
            for table_name in tables_to_check:
                # 检查字段是否存在
                field_exists = self.check_field_exists(table_name, safe_field_name)
                
                if field_exists:
                    # 获取该表中的所有不同值
                    values = self.get_distinct_values(table_name, safe_field_name)
                    
                    # 添加到结果中
                    for value in values:
                        if value and value not in results:
                            results.append(value)
                    
                    # 如果已经找到值，不需要继续查找其他表
                    if results:
                        break
            
            if not results:
                logger.warning(f"在所有表中都找不到字段: {field_name}")
            
        except Exception as e:
            logger.error(f"获取属性值失败: {e}")
        
        return results
    
    def check_field_exists(self, table_name: str, field_name: str) -> bool:
        """检查表中是否存在该字段"""
        try:
            query = f"""
            SELECT COUNT(*) AS field_exists
            FROM information_schema.columns
            WHERE table_schema = '{self.config['database']}'
              AND table_name = '{table_name}'
              AND column_name = '{field_name}'
            """
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            field_exists = cursor.fetchone()['field_exists'] > 0
            cursor.close()
            
            return field_exists
        except Exception as e:
            logger.error(f"检查字段失败: {e}")
            return False
    
    def get_distinct_values(self, table_name: str, field_name: str) -> List[str]:
        try:
            query = f"""
            SELECT DISTINCT `{field_name}` AS value
            FROM {table_name}
            WHERE `{field_name}` IS NOT NULL AND `{field_name}` != ''
            ORDER BY `{field_name}`
            """
            
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query)
            
            values = []
            for row in cursor.fetchall():
                value = row['value']
                if value:
                    values.append(value)
            
            cursor.close()
            return values
        except Exception as e:
            logger.error(f"获取字段值失败: {e}")
            return [] 