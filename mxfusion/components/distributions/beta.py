# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
#   Licensed under the Apache License, Version 2.0 (the "License").
#   You may not use this file except in compliance with the License.
#   A copy of the License is located at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   or in the "license" file accompanying this file. This file is distributed
#   on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#   express or implied. See the License for the specific language governing
#   permissions and limitations under the License.
# ==============================================================================


from ...common.config import get_default_MXNet_mode
from .univariate import UnivariateDistribution


class Beta(UnivariateDistribution):
    """
    The one-dimensional beta distribution. The beta distribution can be defined over a scalar random variable or an
    array of random variables. In case of an array of random variables, a and b are broadcasted to the
    shape of the output random variable (array).

    :param alpha: a parameter (alpha) of the beta distribution.
    :type alpha: Variable
    :param beta: b parameter (beta) of the beta distribution.
    :type beta: Variable
    :param rand_gen: the random generator (default: MXNetRandomGenerator).
    :type rand_gen: RandomGenerator
    :param dtype: the data type for float point numbers.
    :type dtype: numpy.float32 or numpy.float64
    :param ctx: the mxnet context (default: None/current context).
    :type ctx: None or mxnet.cpu or mxnet.gpu
    """
    def __init__(self, alpha, beta, rand_gen=None, dtype=None, ctx=None):
        inputs = [('alpha', alpha), ('beta', beta)]
        input_names = [k for k, _ in inputs]
        output_names = ['random_variable']
        super(Beta, self).__init__(inputs=inputs, outputs=None,
                                   input_names=input_names,
                                   output_names=output_names,
                                   rand_gen=rand_gen, dtype=dtype, ctx=ctx)

    def log_pdf_impl(self, alpha, beta, random_variable, F=None):
        """
        Computes the logarithm of the probability density function (PDF) of the beta distribution.

        :param alpha: the a parameter (alpha) of the beta distribution.
        :type alpha: MXNet NDArray or MXNet Symbol
        :param beta: the b parameter (beta) of the beta distributions.
        :type beta: MXNet NDArray or MXNet Symbol
        :param random_variable: the random variable of the beta distribution.
        :type random_variable: MXNet NDArray or MXNet Symbol
        :param F: the MXNet computation mode (mxnet.symbol or mxnet.ndarray).
        :returns: log pdf of the distribution.
        :rtypes: MXNet NDArray or MXNet Symbol
        """
        F = get_default_MXNet_mode() if F is None else F

        log_x = F.log(random_variable)
        log_1_minus_x = F.log(1 - random_variable)
        log_beta_ab = F.gammaln(alpha) + F.gammaln(beta) - \
            F.gammaln(alpha + beta)

        log_likelihood = F.broadcast_add((alpha - 1) * log_x, ((beta - 1) * log_1_minus_x)) - log_beta_ab
        return log_likelihood

    def draw_samples_impl(self, alpha, beta, rv_shape, num_samples=1, F=None):
        """
        Draw samples from the beta distribution.

        If X and Y are independent, with $X \sim \Gamma(\alpha, \theta)$ and $Y \sim \Gamma(\beta, \theta)$ then
        $\frac {X}{X+Y}}\sim \mathrm {B} (\alpha ,\beta ).}$

        :param alpha: the a parameter (alpha) of the beta distribution.
        :type alpha: MXNet NDArray or MXNet Symbol
        :param beta: the b parameter (beta) of the beta distributions.
        :type beta: MXNet NDArray or MXNet Symbol
        :param rv_shape: the shape of each sample.
        :type rv_shape: tuple
        :param num_samples: the number of drawn samples (default: one).
        :type num_samples: int
        :param F: the MXNet computation mode (mxnet.symbol or mxnet.ndarray).
        :returns: a set samples of the beta distribution.
        :rtypes: MXNet NDArray or MXNet Symbol
        """
        F = get_default_MXNet_mode() if F is None else F

        if alpha.shape != (num_samples, ) + rv_shape:
            raise ValueError("Shape mismatch between inputs {} and random variable {}".format(
                alpha.shape, (num_samples, ) + rv_shape))

        # Note output shape is determined by input dimensions
        out_shape = ()  # (num_samples,) + rv_shape

        ones = F.ones_like(alpha)

        # Sample X from Gamma(a, 1)
        x = self._rand_gen.sample_gamma(
            alpha=alpha, beta=ones, shape=out_shape, dtype=self.dtype,
            ctx=self.ctx, F=F)

        # Sample Y from Gamma(b, 1)
        y = self._rand_gen.sample_gamma(
            alpha=beta, beta=ones, shape=out_shape, dtype=self.dtype,
            ctx=self.ctx, F=F)

        # Return X / (X + Y)
        return F.broadcast_div(x, F.broadcast_add(x, y))

    @staticmethod
    def define_variable(alpha=1., beta=1., shape=None, rand_gen=None,
                        dtype=None, ctx=None):
        """
        Creates and returns a random variable drawn from a beta distribution.

        :param a: The a parameter (alpha) of the distribution.
        :param b: The b parameter (beta) of the distribution.
        :param shape: the shape of the random variable(s).
        :type shape: tuple or [tuple]
        :param rand_gen: the random generator (default: MXNetRandomGenerator).
        :type rand_gen: RandomGenerator
        :param dtype: the data type for float point numbers.
        :type dtype: numpy.float32 or numpy.float64
        :param ctx: the mxnet context (default: None/current context).
        :type ctx: None or mxnet.cpu or mxnet.gpu
        :returns: the random variables drawn from the beta distribution.
        :rtypes: Variable
        """
        beta = Beta(alpha=alpha, beta=beta, rand_gen=rand_gen, dtype=dtype,
                    ctx=ctx)
        beta._generate_outputs(shape=shape)
        return beta.random_variable
