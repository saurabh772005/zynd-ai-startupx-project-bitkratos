import type {
    IWebhookFunctions,
    IDataObject,
    INodeType,
    INodeTypeDescription,
    IWebhookResponseData,
} from 'n8n-workflow';
import { NodeConnectionTypes } from 'n8n-workflow';
import { settlePayment, facilitator } from 'thirdweb/x402';
import { createThirdwebClient } from 'thirdweb';
import {
    arbitrum,
    arbitrumSepolia,
    base,
    // baseSepolia,
    ethereum,
    sepolia,
    polygon,
    optimism,
    baseSepolia,
} from 'thirdweb/chains';

export class X402Webhook implements INodeType {
    description: INodeTypeDescription = {
        displayName: 'X402 Webhook',
        name: 'x402Webhook',
        icon: 'fa:dollar-sign',
        group: ['trigger'],
        version: 1,
        subtitle: '={{$parameter["path"]}} - Payment ({{$parameter["price"]}})',
        description: 'Webhook that requires x402 payment using thirdweb',
        defaults: {
            name: 'X402 Webhook',
        },
        inputs: [],
        outputs: [NodeConnectionTypes.Main],
        webhooks: [
            {
                name: 'default',
                httpMethod: '={{$parameter["httpMethod"]}}',
                responseMode: 'onReceived',
                path: '={{$parameter["path"]}}',
            },
        ],
        properties: [
            {
                displayName:
                    'This node uses thirdweb x402 for payment verification. Requires thirdweb secret key.',
                name: 'notice',
                type: 'notice',
                default: '',
            },
            {
                displayName: 'HTTP Method',
                name: 'httpMethod',
                type: 'options',
                options: [
                    { name: 'GET', value: 'GET' },
                    { name: 'POST', value: 'POST' },
                    { name: 'PUT', value: 'PUT' },
                    { name: 'DELETE', value: 'DELETE' },
                    { name: 'PATCH', value: 'PATCH' },
                ],
                default: 'POST',
                required: true,
                description: 'The HTTP method to listen for',
            },
            {
                displayName: 'Path',
                name: 'path',
                type: 'string',
                default: 'webhook',
                required: true,
                description: 'The path to listen on (e.g., "webhook" for /webhook)',
            },
            {
                displayName: 'Thirdweb Secret Key',
                name: 'thirdwebSecretKey',
                type: 'string',
                typeOptions: { password: true },
                default: '',
                placeholder: 'Use THIRDWEB_SECRET_KEY env var or enter here',
                description:
                    'Your thirdweb secret key (from https://thirdweb.com/dashboard). Can also use THIRDWEB_SECRET_KEY environment variable.',
            },
            {
                displayName: 'Server Wallet Address',
                name: 'serverWalletAddress',
                type: 'string',
                default: '',
                required: true,
                placeholder: '0x1234567890123456789012345678901234567890',
                description: 'The wallet address that will receive payments',
            },
            {
                displayName: 'Price',
                name: 'price',
                type: 'string',
                default: '$0.01',
                required: true,
                placeholder: '$0.01',
                description: 'Payment price (e.g., $0.01 for USDC, 0.001 for native token)',
            },
            {
                displayName: 'Network',
                name: 'network',
                type: 'options',
                options: [
                    { name: 'Base', value: 'base' },
                    { name: 'Base Sepolia (Testnet)', value: 'base-sepolia' },
                    { name: 'Ethereum', value: 'ethereum' },
                    { name: 'Ethereum Sepolia', value: 'sepolia' },
                    { name: 'Polygon', value: 'polygon' },
                    { name: 'Arbitrum', value: 'arbitrum' },
                    { name: 'Arbitrum Sepolia', value: 'arbitrum-sepolia' },
                    { name: 'Optimism', value: 'optimism' },
                ],
                default: 'base-sepolia',
                required: true,
                description: 'Blockchain network to accept payments on',
            },
            {
                displayName: 'Options',
                name: 'options',
                type: 'collection',
                placeholder: 'Add Option',
                default: {},
                options: [
                    {
                        displayName: 'Require Payment',
                        name: 'requirePayment',
                        type: 'boolean',
                        default: true,
                        description: 'Whether to require payment before processing webhook',
                    },
                    {
                        displayName: 'Description',
                        name: 'description',
                        type: 'string',
                        default: 'Access to webhook endpoint',
                        description: 'Description of what the payment is for',
                    },
                    {
                        displayName: 'MIME Type',
                        name: 'mimeType',
                        type: 'string',
                        default: 'application/json',
                        description: 'Response content type',
                    },
                    {
                        displayName: 'Max Timeout Seconds',
                        name: 'maxTimeoutSeconds',
                        type: 'number',
                        default: 300,
                        description: 'Maximum time in seconds for payment to be valid',
                    },
                    {
                        displayName: 'Include Payment Details',
                        name: 'includePaymentDetails',
                        type: 'boolean',
                        default: true,
                        description: 'Whether to include payment details in workflow data',
                    },
                ],
            },
        ],
    };

    async webhook(this: IWebhookFunctions): Promise<IWebhookResponseData> {
        try {
            const getNetworkChain = (networkName: string): any => {
                const chains: Record<string, any> = {
                    base,
                    'base-sepolia': baseSepolia,
                    ethereum,
                    sepolia,
                    polygon,
                    arbitrum,
                    'arbitrum-sepolia': arbitrumSepolia,
                    optimism,
                };

                const chain = chains[networkName];
                if (!chain) {
                    throw new Error(`Unsupported network: ${networkName}`);
                }

                return chain;
            };

            const sendJsonResponse = (statusCode: number, data: any): IWebhookResponseData => {
                const res = this.getResponseObject();
                res.writeHead(statusCode, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify(data));

                return {
                    noWebhookResponse: true,
                };
            };

            const options = this.getNodeParameter('options', {}) as IDataObject;
            const requirePayment = options.requirePayment !== false;

            const bodyData = this.getBodyData();
            const headers = this.getHeaderData();
            const queryData = this.getQueryData() as IDataObject;

            // NO PAYMENT REQUIRED - Send response manually
            if (!requirePayment) {
                const returnData: IDataObject[] = [
                    {
                        body: bodyData,
                        headers,
                        query: queryData,
                    },
                ];

                return sendJsonResponse(200, {
                    success: true,
                    data: returnData[0],
                });
            }

            // Validate thirdweb secret key
            let thirdwebSecretKey = this.getNodeParameter('thirdwebSecretKey') as string;
            if (!thirdwebSecretKey) {
                thirdwebSecretKey = process.env.THIRDWEB_SECRET_KEY || '';
            }

            if (!thirdwebSecretKey) {
                return sendJsonResponse(500, {
                    error: 'Configuration Error',
                    details: 'Thirdweb secret key is required. Set THIRDWEB_SECRET_KEY environment variable or provide in node configuration.',
                });
            }

            const serverWalletAddress = this.getNodeParameter('serverWalletAddress') as string;
            const price = this.getNodeParameter('price') as string;
            const networkName = this.getNodeParameter('network') as string;
            const httpMethod = this.getNodeParameter('httpMethod') as string;

            const description = (options.description as string) || 'Access to webhook endpoint';
            const mimeType = (options.mimeType as string) || 'application/json';
            const maxTimeoutSeconds = (options.maxTimeoutSeconds as number) || 300;

            const network = getNetworkChain(networkName);

            const client = createThirdwebClient({
                clientId: "580a983d5e6e9807f40b9f18678c02ee",
                secretKey: thirdwebSecretKey,
            });

            const thirdwebFacilitator = facilitator({
                client,
                serverWalletAddress,
            });

            const paymentData = headers['x-payment'] as string | undefined;
            const webhookUrl = this.getNodeWebhookUrl('default') as string;

            const result = await settlePayment({
                resourceUrl: webhookUrl,
                method: httpMethod,
                paymentData,
                payTo: serverWalletAddress,
                network,
                price,
                facilitator: thirdwebFacilitator,
                routeConfig: {
                    description,
                    mimeType,
                    maxTimeoutSeconds,
                },
            });

            console.log('settlePayment result:', JSON.stringify(result, null, 2));

            if (result.status === 200) {
                // PAYMENT VERIFIED - Send response manually and trigger workflow
                const paymentDetails = options.includePaymentDetails
                    ? {
                        payment: {
                            verified: true,
                            verifiedAt: new Date().toISOString(),
                            network: networkName,
                            price,
                            payTo: serverWalletAddress,
                        },
                    }
                    : {};

                const returnData: IDataObject[] = [
                    {
                        body: bodyData,
                        headers,
                        query: queryData,
                        ...paymentDetails,
                    },
                ];

                // Send HTTP response
                const res = this.getResponseObject();
                res.writeHead(200, { 'Content-Type': 'application/json' });
                res.end(JSON.stringify({
                    success: true,
                    message: 'Payment verified',
                }));

                // Return workflow data
                return {
                    noWebhookResponse: true,
                    workflowData: [this.helpers.returnJsonArray(returnData)],
                };
            } else {
                // PAYMENT VERIFICATION FAILED - Return x402 protocol response
                let x402Response: any;

                try {
                    if (result.responseBody) {
                        x402Response = typeof result.responseBody === 'string'
                            ? JSON.parse(result.responseBody)
                            : result.responseBody;
                    } else {
                        x402Response = {
                            x402Version: 1,
                            error: 'Payment verification failed',
                        };
                    }

                } catch (parseError) {
                    x402Response = {
                        x402Version: 1,
                        error: 'Payment verification failed',
                    };
                }

                const res = this.getResponseObject();
                const responseHeaders = {
                    'Content-Type': 'application/json',
                    ...(result.responseHeaders || {}),
                };

                res.writeHead(result.status, responseHeaders);
                res.end(JSON.stringify(x402Response));

                return {
                    noWebhookResponse: true,
                };
            }

        } catch (error) {
            // ERROR HANDLER - Send error response manually
            const res = this.getResponseObject();
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({
                error: 'Payment processing error',
                message: error.message || 'An unexpected error occurred',
            }));

            return {
                noWebhookResponse: true,
            };
        }
    }
}