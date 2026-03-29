// Type declaration for optional onnxruntime-node dependency
// The package may not be installed — the app handles this gracefully
declare module "onnxruntime-node" {
  export class InferenceSession {
    static create(path: string): Promise<InferenceSession>;
    inputNames: string[];
    outputNames: string[];
    run(feeds: Record<string, any>): Promise<Record<string, any>>;
  }

  export class Tensor {
    constructor(type: string, data: Float32Array, dims: number[]);
    data: Float32Array;
  }
}
