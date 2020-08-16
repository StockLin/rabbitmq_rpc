import time
import functools
import threading
import pika
from interfaces.IConsumer import IConsumer
from interfaces.ICallback import ICallback


class RpcThreadingConsumer(IConsumer):
    
    def __init__(self, conn_config=None, callback=None):
        self._host = conn_config.host if conn_config.host else ""
        self._port = conn_config.port
        self._username = conn_config.username if conn_config.username else ""
        self._password = conn_config.password if conn_config.password else ""
        self._queue = conn_config.queue if conn_config.queue else ""
        self._vhost = conn_config.vhost
        self._prefetch_count = conn_config.prefetch_count
        self._callback = callback
        self._connection = None
        self._channel = None
        
        
    def _build_connection(self):
        try:
            credentials = pika.PlainCredentials(username=self._username, password=self._password)
            properties = {
                "connection_name":"connecting queue: {}".format(self._queue)
            }
            parameters = pika.ConnectionParameters(
                host = self._host,
                port = self._port,
                virtual_host = self._vhost,
                credentials = credentials,
                heartbeat = 600,
                client_properties = properties
            )
            
            self._connection = pika.BlockingConnection(parameters)
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self._queue, durable=True)
            self._channel.basic_qos(prefetch_count=self._prefetch_count)
            
        except Exception as e:
            raise e
        
    def _ack_message(self, ch, delivery_tag, props, response):
        """Note that `ch` must be the same pika channel instance via which
        the message being ACKed was retrieved (AMQP protocol constraint).
        """
        try:
            if ch.is_open:
                ch.basic_publish(
                    exchange = "",
                    routing_key = props.reply_to,
                    properties = pika.BasicProperties(
                        correlation_id = props.correlation_id
                    ),
                    body = str(response)
                )
                
            else:
                # Channel is already closed, so we can't ACK this message;
                # log and/or do something that makes sense for your app in this case.
                pass
        
        except Exception as e:
            raise e
        
        finally:
            if self._channel.is_open:
                ch.basic_ack(delivery_tag)

    def _callback_procedure(self, conn, ch, delivery_tag, props, body):
        try:
            request_data = body.decode("utf-8")
            response = self._callback.callback(request_data)
            cb = functools.partial(self._ack_message, ch, delivery_tag, props, response)
            conn.add_callback_threadsafe(cb)
            
        except Exception as e:
            response = str(e)
            cb = functools.partial(self._ack_message, ch, delivery_tag, props, response)
            conn.add_callback_threadsafe(cb)
        
    def _on_message(self, ch, method, props, body, args):
        (conn, thrds) = args
        delivery_tag = method.delivery_tag
        
        worker = threading.Thread(target=self._callback_procedure, args=(conn, ch, delivery_tag, props, body))
        worker.start()
        thrds.append(worker)
        
    def start(self, callback=None):
        try:
            if not self._connection:
                self._build_connection()
                
            self._callback = callback
            if not self._callback:
                print("Service required callback function.")
                
            else:
                threads = []
                on_message_callback = functools.partial(self._on_message, args=[self._connection, threads])
                self._channel.basic_consumer(self._queue, on_message_callback)
                
                print("[.] START AWAITING......")
                self._channel.start_consuming()
            
        except Exception as e:
            print("unexcepted error, when start conumer... \n".format(str(e)))
            raise e
        
        finally:
            # wait for all to complete
            for thread in threads:
                thread.join()
                
            print("<<=============== CLOSE CONNECTION ==============>>")
            self._connection.close()
            self._connection = None
    
    def stop(self):
        try:
            if self._channel:
                
                self._channel.stop_consuming()
                print("consumer stop complete.")
                
        except Exception as e:
            raise e