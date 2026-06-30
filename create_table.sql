-- 创建表：barcode_base_info_top96_incre_msy_20260515
CREATE TABLE `barcode_base_info_top96_incre_msy_20260515` (
  `item_barcode` varchar(50) NOT NULL COMMENT '商品条码',
  `item_name` varchar(255) DEFAULT NULL COMMENT '商品名称',
  `product_name` varchar(255) DEFAULT NULL COMMENT '产品名称',
  `brand` varchar(100) DEFAULT NULL COMMENT '品牌',
  `group` varchar(100) DEFAULT NULL COMMENT '分组',
  `manufacturer` varchar(255) DEFAULT NULL COMMENT '制造商',
  `category` varchar(100) DEFAULT NULL COMMENT '类别',
  `median_price` decimal(10,2) DEFAULT NULL COMMENT '中位数价格',
  `first_order_date` date DEFAULT NULL COMMENT '首次下单日期',
  `screenshot_path` varchar(500) DEFAULT NULL COMMENT '截图路径',
  PRIMARY KEY (`item_barcode`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='69开头TOP96增量MSY商品信息表20260515';
